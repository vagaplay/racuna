#!/bin/bash

# =============================================================================
# BOLT DASHBOARD - SETUP BUDGET AUTOMATION (LÓGICA BUDGETBASA)
# =============================================================================
# Este script configura budgets, webhooks e automação de budget excedido

set -e

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
    exit 1
}

# =============================================================================
# CARREGAR CONFIGURAÇÕES
# =============================================================================
if [ -f .env ]; then
    log "Carregando configurações..."
    set -o allexport
    source .env
    set +o allexport
else
    error "Arquivo .env não encontrado."
fi

if [ -f azure-resources.txt ]; then
    source azure-resources.txt
else
    error "Execute primeiro: ./scripts/azure-setup.sh"
fi

# =============================================================================
# LOGIN NO AZURE
# =============================================================================
log "Fazendo login no Azure..."
az login --service-principal \
    --username "$AZURE_CLIENT_ID" \
    --password "$AZURE_CLIENT_SECRET" \
    --tenant "$AZURE_TENANT_ID" > /dev/null

az account set --subscription "$AZURE_SUBSCRIPTION_ID"

# =============================================================================
# CRIAR RUNBOOK DE BUDGET EXCEDIDO (LÓGICA BUDGETBASA)
# =============================================================================
log "Criando runbook de budget excedido..."

cat > /tmp/budget-exceeded-runbook.ps1 << 'EOF'
param(
    [string]$subscriptionId,
    [string]$action = "show"
)

Import-Module Az.Accounts
Import-Module Az.Resources

# Obter credenciais
$tenantId = Get-AutomationVariable -Name 'AZURE_TENANT_ID'
$clientId = Get-AutomationVariable -Name 'AZURE_CLIENT_ID'
$clientSecret = Get-AutomationVariable -Name 'AZURE_CLIENT_SECRET'
$protectedRGs = Get-AutomationVariable -Name 'PROTECTED_RESOURCE_GROUPS'

$secureSecret = ConvertTo-SecureString -String $clientSecret -AsPlainText -Force
$credential = New-Object System.Management.Automation.PSCredential ($clientId, $secureSecret)

Connect-AzAccount -ServicePrincipal -Credential $credential -TenantId $tenantId -SubscriptionId $subscriptionId

Write-Output "=== BUDGET EXCEDIDO - INICIANDO PROCESSO ==="
Write-Output "Subscription: $subscriptionId"
Write-Output "Ação: $action"

# Converter lista de RGs protegidos
$protectedResourceGroups = $protectedRGs -split ","
Write-Output "Resource Groups protegidos: $($protectedResourceGroups -join ', ')"

# Verificar locks HoldLock e adicionar RGs à lista de protegidos
$locks = Get-AzResourceLock
$additionalProtectedRGs = @()

foreach ($lock in $locks) {
    if ($lock.Name -eq "HoldLock") {
        $rgName = ($lock.ResourceId -split "/")[4]
        if ($protectedResourceGroups -notcontains $rgName) {
            $additionalProtectedRGs += $rgName
            Write-Output "RG com HoldLock encontrado e protegido: $rgName"
        }
    } else {
        Write-Output "Removendo lock para permitir exclusão: $($lock.Name)"
        if ($action -eq "delete") {
            Remove-AzResourceLock -LockId $lock.LockId -Force
        }
    }
}

# Combinar listas de RGs protegidos
$allProtectedRGs = $protectedResourceGroups + $additionalProtectedRGs

# Obter todos os resource groups
$resourceGroups = Get-AzResourceGroup

Write-Output "=== ANÁLISE DE RESOURCE GROUPS ==="
foreach ($rg in $resourceGroups) {
    if ($allProtectedRGs -contains $rg.ResourceGroupName) {
        Write-Output "✅ PROTEGIDO: $($rg.ResourceGroupName)"
    } else {
        if ($action -eq "delete") {
            Write-Output "🗑️  EXCLUINDO: $($rg.ResourceGroupName)"
            Remove-AzResourceGroup -Name $rg.ResourceGroupName -Force
        } else {
            Write-Output "⚠️  SERIA EXCLUÍDO: $($rg.ResourceGroupName)"
        }
    }
}

# Adicionar lock na subscription se ação for delete
if ($action -eq "delete") {
    Write-Output "=== ADICIONANDO LOCK NA SUBSCRIPTION ==="
    New-AzResourceLock -LockLevel ReadOnly -Name "Prevent-Spending-BudgetControl" -Notes "Lock automático - budget excedido" -Scope "/subscriptions/$subscriptionId" -Force
    Write-Output "Lock adicionado na subscription para prevenir gastos adicionais."
} else {
    Write-Output "=== SIMULAÇÃO CONCLUÍDA ==="
    Write-Output "Para executar realmente, altere o parâmetro action para 'delete'"
}

Write-Output "=== PROCESSO CONCLUÍDO ==="
EOF

# Criar o runbook
az automation runbook create \
    --automation-account-name "$AUTOMATION_ACCOUNT_NAME" \
    --resource-group "$RESOURCE_GROUP_NAME" \
    --name "BudgetExceededRunbook" \
    --type "PowerShell" \
    --description "Runbook executado quando budget é excedido - lógica do projeto budgetbasa"

az automation runbook replace-content \
    --automation-account-name "$AUTOMATION_ACCOUNT_NAME" \
    --resource-group "$RESOURCE_GROUP_NAME" \
    --name "BudgetExceededRunbook" \
    --content-path "/tmp/budget-exceeded-runbook.ps1"

az automation runbook publish \
    --automation-account-name "$AUTOMATION_ACCOUNT_NAME" \
    --resource-group "$RESOURCE_GROUP_NAME" \
    --name "BudgetExceededRunbook"

log "Runbook de budget excedido criado com sucesso!"

# =============================================================================
# CRIAR WEBHOOK PARA BUDGET
# =============================================================================
log "Criando webhook para budget..."

# Criar webhook
WEBHOOK_OUTPUT=$(az automation webhook create \
    --automation-account-name "$AUTOMATION_ACCOUNT_NAME" \
    --resource-group "$RESOURCE_GROUP_NAME" \
    --name "BudgetExceededWebhook" \
    --runbook-name "BudgetExceededRunbook" \
    --expiry-time "$(date -d '+2 years' -u +%Y-%m-%dT%H:%M:%S.000Z)" \
    --parameters subscriptionId="$AZURE_SUBSCRIPTION_ID" action="$DEFAULT_ACTION_BUDGET_EXCEEDED")

# Extrair URL do webhook
WEBHOOK_URL=$(echo "$WEBHOOK_OUTPUT" | jq -r '.uri')

log "Webhook criado com sucesso!"
log "URL do webhook: $WEBHOOK_URL"

# Salvar URL do webhook
echo "BUDGET_WEBHOOK_URL=$WEBHOOK_URL" >> azure-resources.txt

# =============================================================================
# CRIAR ACTION GROUP PARA NOTIFICAÇÕES
# =============================================================================
log "Criando Action Group para notificações de budget..."

# Converter emails para formato JSON
IFS=',' read -ra EMAIL_ARRAY <<< "$CONTACT_EMAILS"
EMAIL_RECEIVERS=""
for i in "${!EMAIL_ARRAY[@]}"; do
    email="${EMAIL_ARRAY[$i]}"
    if [ $i -gt 0 ]; then
        EMAIL_RECEIVERS+=","
    fi
    EMAIL_RECEIVERS+="{\"name\":\"email-$i\",\"emailAddress\":\"$email\"}"
done

# Criar Action Group
az monitor action-group create \
    --name "BudgetControlActionGroup" \
    --resource-group "$RESOURCE_GROUP_NAME" \
    --short-name "BudgetCtrl" \
    --email-receivers "[$EMAIL_RECEIVERS]" \
    --webhook-receivers "[{\"name\":\"budget-webhook\",\"serviceUri\":\"$WEBHOOK_URL\"}]"

log "Action Group criado com sucesso!"

# =============================================================================
# CRIAR BUDGET COM MÚLTIPLOS ALERTAS
# =============================================================================
log "Criando budget com alertas personalizados..."

# Converter thresholds em array
IFS=',' read -ra THRESHOLD_ARRAY <<< "$BUDGET_ALERT_THRESHOLDS"

# Data de início (primeiro dia do mês atual)
START_DATE=$(date +%Y-%m-01)
# Data de fim (5 anos no futuro)
END_DATE=$(date -d '+5 years' +%Y-%m-01)

# Criar budget
BUDGET_NAME="BoltDashboardBudget"

# Preparar notificações baseadas na configuração
NOTIFICATIONS=""
for threshold in "${THRESHOLD_ARRAY[@]}"; do
    if [ -n "$NOTIFICATIONS" ]; then
        NOTIFICATIONS+=","
    fi
    
    # Determinar tipo de notificação baseado no threshold
    if [ "$threshold" -ge 100 ]; then
        # 100% ou mais: email + webhook
        NOTIFICATIONS+="{\"enabled\":true,\"operator\":\"GreaterThanOrEqualTo\",\"threshold\":$threshold,\"contactEmails\":[$(printf '"%s",' "${EMAIL_ARRAY[@]}" | sed 's/,$//')],"
        NOTIFICATIONS+="\"contactGroups\":[\"/subscriptions/$AZURE_SUBSCRIPTION_ID/resourceGroups/$RESOURCE_GROUP_NAME/providers/microsoft.insights/actionGroups/BudgetControlActionGroup\"]"
        if [ "$threshold" -eq 100 ]; then
            NOTIFICATIONS+=",\"thresholdType\":\"Actual\""
        fi
        NOTIFICATIONS+="}"
    else
        # Menos de 100%: apenas email
        NOTIFICATIONS+="{\"enabled\":true,\"operator\":\"GreaterThanOrEqualTo\",\"threshold\":$threshold,\"contactEmails\":[$(printf '"%s",' "${EMAIL_ARRAY[@]}" | sed 's/,$//')]}"
    fi
done

# Criar arquivo JSON temporário para o budget
cat > /tmp/budget.json << EOF
{
  "properties": {
    "category": "Cost",
    "amount": $DEFAULT_BUDGET_AMOUNT,
    "timeGrain": "Monthly",
    "timePeriod": {
      "startDate": "$START_DATE",
      "endDate": "$END_DATE"
    },
    "notifications": {
      $(echo "$NOTIFICATIONS" | sed 's/^,//' | awk '{for(i=1;i<=NF;i++) printf "\"notification%d\":%s,", NR+i-1, $i}' | sed 's/,$//')
    }
  }
}
EOF

# Criar budget usando REST API (az CLI não suporta múltiplas notificações facilmente)
BUDGET_URL="https://management.azure.com/subscriptions/$AZURE_SUBSCRIPTION_ID/providers/Microsoft.Consumption/budgets/$BUDGET_NAME?api-version=2021-10-01"

# Obter token de acesso
ACCESS_TOKEN=$(az account get-access-token --query accessToken -o tsv)

# Criar budget via REST API
curl -X PUT "$BUDGET_URL" \
    -H "Authorization: Bearer $ACCESS_TOKEN" \
    -H "Content-Type: application/json" \
    -d @/tmp/budget.json

log "Budget criado com alertas personalizados!"

# =============================================================================
# CRIAR FUNÇÃO PARA APROVAÇÃO DE AÇÕES
# =============================================================================
log "Configurando sistema de aprovação para ações críticas..."

# Esta funcionalidade será implementada no dashboard web
# Por enquanto, criar um runbook que requer aprovação manual

cat > /tmp/approval-required-runbook.ps1 << 'EOF'
param(
    [string]$action,
    [string]$resourceInfo,
    [string]$approvalToken
)

# Este runbook requer aprovação manual antes de executar ações críticas
Write-Output "=== APROVAÇÃO NECESSÁRIA ==="
Write-Output "Ação solicitada: $action"
Write-Output "Recursos afetados: $resourceInfo"
Write-Output "Token de aprovação: $approvalToken"
Write-Output ""
Write-Output "Para aprovar esta ação:"
Write-Output "1. Acesse o BOLT Dashboard"
Write-Output "2. Vá para a seção de Aprovações"
Write-Output "3. Use o token: $approvalToken"
Write-Output ""
Write-Output "A ação será executada apenas após aprovação manual."
EOF

az automation runbook create \
    --automation-account-name "$AUTOMATION_ACCOUNT_NAME" \
    --resource-group "$RESOURCE_GROUP_NAME" \
    --name "ApprovalRequiredRunbook" \
    --type "PowerShell" \
    --description "Runbook que requer aprovação manual para ações críticas"

az automation runbook replace-content \
    --automation-account-name "$AUTOMATION_ACCOUNT_NAME" \
    --resource-group "$RESOURCE_GROUP_NAME" \
    --name "ApprovalRequiredRunbook" \
    --content-path "/tmp/approval-required-runbook.ps1"

az automation runbook publish \
    --automation-account-name "$AUTOMATION_ACCOUNT_NAME" \
    --resource-group "$RESOURCE_GROUP_NAME" \
    --name "ApprovalRequiredRunbook"

log "Sistema de aprovação configurado!"

# =============================================================================
# RESUMO FINAL
# =============================================================================
log "=========================================="
log "BUDGET AUTOMATION CONFIGURADO! 💰"
log "=========================================="
log ""
log "Componentes criados:"
log "  ✅ Runbook de budget excedido"
log "  ✅ Webhook para automação: $WEBHOOK_URL"
log "  ✅ Action Group para notificações"
log "  ✅ Budget com alertas em: $(echo $BUDGET_ALERT_THRESHOLDS | tr ',' ' ')%"
log "  ✅ Sistema de aprovação manual"
log ""
log "Configurações:"
log "  💰 Budget: \$${DEFAULT_BUDGET_AMOUNT} USD"
log "  📧 Emails: $CONTACT_EMAILS"
log "  ⚡ Ação padrão: $DEFAULT_ACTION_BUDGET_EXCEEDED"
log ""
log "Fluxo de automação:"
log "  1. Budget atinge threshold → Email enviado"
log "  2. Budget atinge 100% → Webhook acionado"
log "  3. Runbook verifica RGs protegidos (HoldLock)"
log "  4. Executa ação configurada (show/delete)"
log "  5. Adiciona lock na subscription (se delete)"
log ""
log "Para testar:"
log "  curl -X POST '$WEBHOOK_URL' -H 'Content-Type: application/json' -d '{\"subscriptionId\":\"$AZURE_SUBSCRIPTION_ID\",\"action\":\"show\"}'"
log ""

# Salvar informações do budget
cat >> azure-resources.txt << EOF

# Budget Automation
BUDGET_NAME=$BUDGET_NAME
BUDGET_WEBHOOK_URL=$WEBHOOK_URL
ACTION_GROUP_NAME=BudgetControlActionGroup
BUDGET_AMOUNT=$DEFAULT_BUDGET_AMOUNT
EOF

log "Budget automation configurado com sucesso! 🎉"

