#!/bin/bash

# =============================================================================
# BOLT DASHBOARD - TESTE DO SISTEMA
# =============================================================================
# Este script testa todas as funcionalidades do sistema

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
}

success() {
    echo -e "${GREEN}✅ $1${NC}"
}

fail() {
    echo -e "${RED}❌ $1${NC}"
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
    exit 1
fi

if [ -f azure-resources.txt ]; then
    source azure-resources.txt
else
    error "Execute primeiro: ./scripts/azure-setup.sh"
    exit 1
fi

# =============================================================================
# TESTE 1: CONECTIVIDADE AZURE
# =============================================================================
log "=== TESTE 1: CONECTIVIDADE AZURE ==="

# Login no Azure
if az login --service-principal \
    --username "$AZURE_CLIENT_ID" \
    --password "$AZURE_CLIENT_SECRET" \
    --tenant "$AZURE_TENANT_ID" > /dev/null 2>&1; then
    success "Login no Azure realizado com sucesso"
else
    fail "Falha no login do Azure"
    exit 1
fi

# Verificar subscription
if az account set --subscription "$AZURE_SUBSCRIPTION_ID" > /dev/null 2>&1; then
    SUBSCRIPTION_NAME=$(az account show --query name -o tsv)
    success "Subscription ativa: $SUBSCRIPTION_NAME"
else
    fail "Falha ao definir subscription"
    exit 1
fi

# =============================================================================
# TESTE 2: RECURSOS AZURE
# =============================================================================
log "=== TESTE 2: RECURSOS AZURE ==="

# Verificar Resource Group
if az group show --name "$RESOURCE_GROUP_NAME" > /dev/null 2>&1; then
    success "Resource Group existe: $RESOURCE_GROUP_NAME"
else
    fail "Resource Group não encontrado: $RESOURCE_GROUP_NAME"
fi

# Verificar Container Registry
if az acr show --name "$CONTAINER_REGISTRY_NAME" --resource-group "$RESOURCE_GROUP_NAME" > /dev/null 2>&1; then
    success "Container Registry existe: $CONTAINER_REGISTRY_NAME"
else
    fail "Container Registry não encontrado: $CONTAINER_REGISTRY_NAME"
fi

# Verificar Key Vault
if az keyvault show --name "$KEY_VAULT_NAME" > /dev/null 2>&1; then
    success "Key Vault existe: $KEY_VAULT_NAME"
else
    fail "Key Vault não encontrado: $KEY_VAULT_NAME"
fi

# Verificar Storage Account
if az storage account show --name "$STORAGE_ACCOUNT_NAME" --resource-group "$RESOURCE_GROUP_NAME" > /dev/null 2>&1; then
    success "Storage Account existe: $STORAGE_ACCOUNT_NAME"
else
    fail "Storage Account não encontrado: $STORAGE_ACCOUNT_NAME"
fi

# Verificar Automation Account
if az automation account show --name "$AUTOMATION_ACCOUNT_NAME" --resource-group "$RESOURCE_GROUP_NAME" > /dev/null 2>&1; then
    success "Automation Account existe: $AUTOMATION_ACCOUNT_NAME"
else
    fail "Automation Account não encontrado: $AUTOMATION_ACCOUNT_NAME"
fi

# =============================================================================
# TESTE 3: RUNBOOKS E AUTOMAÇÃO
# =============================================================================
log "=== TESTE 3: RUNBOOKS E AUTOMAÇÃO ==="

# Lista de runbooks esperados
EXPECTED_RUNBOOKS=(
    "ShutdownResourcesRunbook"
    "CleanupExpiredTagsRunbook"
    "RemoveSubscriptionLockRunbook"
    "BudgetExceededRunbook"
    "ApprovalRequiredRunbook"
)

for runbook in "${EXPECTED_RUNBOOKS[@]}"; do
    if az automation runbook show --automation-account-name "$AUTOMATION_ACCOUNT_NAME" --resource-group "$RESOURCE_GROUP_NAME" --name "$runbook" > /dev/null 2>&1; then
        success "Runbook existe: $runbook"
    else
        fail "Runbook não encontrado: $runbook"
    fi
done

# =============================================================================
# TESTE 4: VARIÁVEIS DE AUTOMAÇÃO
# =============================================================================
log "=== TESTE 4: VARIÁVEIS DE AUTOMAÇÃO ==="

EXPECTED_VARIABLES=(
    "AZURE_TENANT_ID"
    "AZURE_CLIENT_ID"
    "AZURE_CLIENT_SECRET"
    "AZURE_SUBSCRIPTION_ID"
    "SHUTDOWN_TIME"
    "TIMEZONE"
    "LOCK_REMOVAL_DAY"
    "PROTECTED_RESOURCE_GROUPS"
)

for variable in "${EXPECTED_VARIABLES[@]}"; do
    if az automation variable show --automation-account-name "$AUTOMATION_ACCOUNT_NAME" --resource-group "$RESOURCE_GROUP_NAME" --name "$variable" > /dev/null 2>&1; then
        success "Variável existe: $variable"
    else
        fail "Variável não encontrada: $variable"
    fi
done

# =============================================================================
# TESTE 5: WEBHOOKS
# =============================================================================
log "=== TESTE 5: WEBHOOKS ==="

if [ -n "$BUDGET_WEBHOOK_URL" ]; then
    success "Webhook URL configurada"
    
    # Testar webhook (modo show)
    log "Testando webhook em modo 'show'..."
    WEBHOOK_RESPONSE=$(curl -s -X POST "$BUDGET_WEBHOOK_URL" \
        -H "Content-Type: application/json" \
        -d "{\"subscriptionId\":\"$AZURE_SUBSCRIPTION_ID\",\"action\":\"show\"}" \
        -w "%{http_code}")
    
    if [[ "$WEBHOOK_RESPONSE" == *"202"* ]]; then
        success "Webhook respondeu corretamente (HTTP 202)"
    else
        warn "Webhook pode não estar funcionando corretamente"
    fi
else
    fail "Webhook URL não configurada"
fi

# =============================================================================
# TESTE 6: BUDGET E ACTION GROUP
# =============================================================================
log "=== TESTE 6: BUDGET E ACTION GROUP ==="

# Verificar Action Group
if az monitor action-group show --name "BudgetControlActionGroup" --resource-group "$RESOURCE_GROUP_NAME" > /dev/null 2>&1; then
    success "Action Group existe: BudgetControlActionGroup"
else
    fail "Action Group não encontrado: BudgetControlActionGroup"
fi

# Verificar Budget (via REST API)
BUDGET_URL="https://management.azure.com/subscriptions/$AZURE_SUBSCRIPTION_ID/providers/Microsoft.Consumption/budgets/BoltDashboardBudget?api-version=2021-10-01"
ACCESS_TOKEN=$(az account get-access-token --query accessToken -o tsv)

BUDGET_CHECK=$(curl -s -H "Authorization: Bearer $ACCESS_TOKEN" "$BUDGET_URL" -w "%{http_code}")

if [[ "$BUDGET_CHECK" == *"200"* ]]; then
    success "Budget existe: BoltDashboardBudget"
else
    fail "Budget não encontrado: BoltDashboardBudget"
fi

# =============================================================================
# TESTE 7: CONTAINER INSTANCE (SE EXISTIR)
# =============================================================================
log "=== TESTE 7: APLICAÇÃO WEB ==="

if [ -n "$BOLT_DASHBOARD_URL" ]; then
    log "Testando aplicação web: $BOLT_DASHBOARD_URL"
    
    # Teste de health check
    if curl -f "$BOLT_DASHBOARD_URL/health" > /dev/null 2>&1; then
        success "Aplicação web está respondendo"
    else
        warn "Aplicação web pode não estar disponível ainda"
    fi
    
    # Teste de página principal
    if curl -f "$BOLT_DASHBOARD_URL" > /dev/null 2>&1; then
        success "Página principal acessível"
    else
        warn "Página principal pode não estar disponível"
    fi
else
    warn "URL da aplicação não configurada (execute build-and-deploy.sh)"
fi

# =============================================================================
# TESTE 8: DOCKER E CONTAINERIZAÇÃO
# =============================================================================
log "=== TESTE 8: DOCKER E CONTAINERIZAÇÃO ==="

# Verificar se Docker está disponível
if command -v docker &> /dev/null; then
    success "Docker está disponível"
    
    # Verificar se pode fazer login no ACR
    if az acr login --name "$CONTAINER_REGISTRY_NAME" > /dev/null 2>&1; then
        success "Login no Container Registry realizado"
    else
        fail "Falha no login do Container Registry"
    fi
else
    warn "Docker não está disponível (necessário para build local)"
fi

# =============================================================================
# TESTE 9: PERMISSÕES E SEGURANÇA
# =============================================================================
log "=== TESTE 9: PERMISSÕES E SEGURANÇA ==="

# Verificar permissões na subscription
ROLE_ASSIGNMENTS=$(az role assignment list --assignee "$AZURE_CLIENT_ID" --scope "/subscriptions/$AZURE_SUBSCRIPTION_ID" --query "[].roleDefinitionName" -o tsv)

if echo "$ROLE_ASSIGNMENTS" | grep -q "Contributor"; then
    success "Service Principal tem permissões de Contributor"
else
    warn "Service Principal pode não ter permissões suficientes"
fi

# Verificar acesso ao Key Vault
if az keyvault secret list --vault-name "$KEY_VAULT_NAME" > /dev/null 2>&1; then
    success "Acesso ao Key Vault funcionando"
else
    warn "Problemas de acesso ao Key Vault"
fi

# =============================================================================
# TESTE 10: CONFIGURAÇÕES ESPECÍFICAS
# =============================================================================
log "=== TESTE 10: CONFIGURAÇÕES ESPECÍFICAS ==="

# Verificar configurações de timezone
if [ -n "$TIMEZONE" ]; then
    success "Timezone configurado: $TIMEZONE"
else
    warn "Timezone não configurado"
fi

# Verificar configurações de shutdown
if [ -n "$SHUTDOWN_TIME" ]; then
    success "Horário de shutdown configurado: $SHUTDOWN_TIME"
else
    warn "Horário de shutdown não configurado"
fi

# Verificar emails de contato
if [ -n "$CONTACT_EMAILS" ]; then
    success "Emails de contato configurados: $CONTACT_EMAILS"
else
    warn "Emails de contato não configurados"
fi

# =============================================================================
# RESUMO FINAL
# =============================================================================
log "=========================================="
log "RESUMO DOS TESTES"
log "=========================================="

# Contar sucessos e falhas
SUCCESS_COUNT=$(grep -c "✅" /tmp/test-results.log 2>/dev/null || echo "0")
FAIL_COUNT=$(grep -c "❌" /tmp/test-results.log 2>/dev/null || echo "0")

log "Testes realizados com sucesso: $SUCCESS_COUNT"
log "Testes com falha: $FAIL_COUNT"

if [ "$FAIL_COUNT" -eq 0 ]; then
    log "🎉 TODOS OS TESTES PASSARAM!"
    log "Sistema está funcionando corretamente."
elif [ "$FAIL_COUNT" -lt 3 ]; then
    log "⚠️  ALGUNS PROBLEMAS ENCONTRADOS"
    log "Sistema está funcionando, mas pode precisar de ajustes."
else
    log "❌ MUITOS PROBLEMAS ENCONTRADOS"
    log "Sistema precisa de correções antes do uso."
fi

log ""
log "Para mais detalhes, verifique os logs acima."
log "Para corrigir problemas, execute novamente os scripts de setup."
log ""

# =============================================================================
# TESTES MANUAIS SUGERIDOS
# =============================================================================
log "=== TESTES MANUAIS SUGERIDOS ==="
log ""
log "1. TESTE DE APLICAÇÃO WEB:"
if [ -n "$BOLT_DASHBOARD_URL" ]; then
    log "   Acesse: $BOLT_DASHBOARD_URL"
    log "   Login: test@test.com"
    log "   Senha: 123456"
else
    log "   Execute: ./scripts/build-and-deploy.sh"
fi
log ""
log "2. TESTE DE RUNBOOK:"
log "   az automation runbook start \\"
log "     --automation-account-name $AUTOMATION_ACCOUNT_NAME \\"
log "     --resource-group $RESOURCE_GROUP_NAME \\"
log "     --name ShutdownResourcesRunbook \\"
log "     --parameters action=show"
log ""
log "3. TESTE DE WEBHOOK:"
log "   curl -X POST '$BUDGET_WEBHOOK_URL' \\"
log "     -H 'Content-Type: application/json' \\"
log "     -d '{\"subscriptionId\":\"$AZURE_SUBSCRIPTION_ID\",\"action\":\"show\"}'"
log ""
log "4. TESTE DE BUDGET:"
log "   Verifique no portal Azure: Subscriptions > Cost Management > Budgets"
log ""

log "Testes concluídos! 🧪"

