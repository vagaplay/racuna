#!/bin/bash

# =============================================================================
# BOLT DASHBOARD - SETUP AUTOMAÇÕES (LÓGICA BUDGETBASA)
# =============================================================================
# Este script configura todas as automações baseadas no projeto budgetbasa

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
# CRIAR RUNBOOK DE SHUTDOWN DE RECURSOS
# =============================================================================
log "Criando runbook de shutdown de recursos..."

cat > /tmp/shutdown-resources-runbook.ps1 << 'EOF'
param(
    [string]$action = "show"
)

# Importar módulos necessários
Import-Module Az.Accounts
Import-Module Az.Resources
Import-Module Az.Compute

# Obter credenciais das variáveis de automação
$tenantId = Get-AutomationVariable -Name 'AZURE_TENANT_ID'
$clientId = Get-AutomationVariable -Name 'AZURE_CLIENT_ID'
$clientSecret = Get-AutomationVariable -Name 'AZURE_CLIENT_SECRET'
$subscriptionId = Get-AutomationVariable -Name 'AZURE_SUBSCRIPTION_ID'
$shutdownTime = Get-AutomationVariable -Name 'SHUTDOWN_TIME'
$timezone = Get-AutomationVariable -Name 'TIMEZONE'

# Converter client secret para SecureString
$secureSecret = ConvertTo-SecureString -String $clientSecret -AsPlainText -Force
$credential = New-Object System.Management.Automation.PSCredential ($clientId, $secureSecret)

# Conectar ao Azure
Connect-AzAccount -ServicePrincipal -Credential $credential -TenantId $tenantId -SubscriptionId $subscriptionId

# Obter hora atual no timezone configurado
$currentTime = [System.TimeZoneInfo]::ConvertTimeBySystemTimeZoneId([DateTime]::UtcNow, $timezone)
$currentHour = $currentTime.ToString("HH:mm")

Write-Output "Hora atual ($timezone): $currentHour"
Write-Output "Hora configurada para shutdown: $shutdownTime"

# Verificar se é hora de fazer shutdown
if ($currentHour -ge $shutdownTime) {
    Write-Output "Iniciando processo de shutdown de recursos..."
    
    # Obter todos os recursos compute
    $vms = Get-AzVM
    $webApps = Get-AzWebApp
    
    foreach ($vm in $vms) {
        $vmStatus = Get-AzVM -ResourceGroupName $vm.ResourceGroupName -Name $vm.Name -Status
        $powerState = ($vmStatus.Statuses | Where-Object {$_.Code -like "PowerState/*"}).DisplayStatus
        
        if ($powerState -eq "VM running") {
            if ($action -eq "delete" -or $action -eq "shutdown") {
                Write-Output "Desligando VM: $($vm.Name)"
                Stop-AzVM -ResourceGroupName $vm.ResourceGroupName -Name $vm.Name -Force
            } else {
                Write-Output "VM que seria desligada: $($vm.Name) (Status: $powerState)"
            }
        } else {
            Write-Output "VM $($vm.Name) já está desligada (Status: $powerState)"
        }
    }
    
    foreach ($webApp in $webApps) {
        if ($webApp.State -eq "Running") {
            if ($action -eq "delete" -or $action -eq "shutdown") {
                Write-Output "Parando Web App: $($webApp.Name)"
                Stop-AzWebApp -ResourceGroupName $webApp.ResourceGroupName -Name $webApp.Name
            } else {
                Write-Output "Web App que seria parada: $($webApp.Name) (Status: $($webApp.State))"
            }
        }
    }
} else {
    Write-Output "Ainda não é hora de fazer shutdown. Hora atual: $currentHour, Hora configurada: $shutdownTime"
}
EOF

# Criar o runbook
az automation runbook create \
    --automation-account-name "$AUTOMATION_ACCOUNT_NAME" \
    --resource-group "$RESOURCE_GROUP_NAME" \
    --name "ShutdownResourcesRunbook" \
    --type "PowerShell" \
    --description "Runbook para desligar recursos compute após horário configurado"

# Importar conteúdo do runbook
az automation runbook replace-content \
    --automation-account-name "$AUTOMATION_ACCOUNT_NAME" \
    --resource-group "$RESOURCE_GROUP_NAME" \
    --name "ShutdownResourcesRunbook" \
    --content-path "/tmp/shutdown-resources-runbook.ps1"

# Publicar runbook
az automation runbook publish \
    --automation-account-name "$AUTOMATION_ACCOUNT_NAME" \
    --resource-group "$RESOURCE_GROUP_NAME" \
    --name "ShutdownResourcesRunbook"

log "Runbook de shutdown criado com sucesso!"

# =============================================================================
# CRIAR RUNBOOK DE LIMPEZA POR TAGS
# =============================================================================
log "Criando runbook de limpeza por tags..."

cat > /tmp/cleanup-expired-tags-runbook.ps1 << 'EOF'
param(
    [string]$action = "show"
)

Import-Module Az.Accounts
Import-Module Az.Resources

# Obter credenciais
$tenantId = Get-AutomationVariable -Name 'AZURE_TENANT_ID'
$clientId = Get-AutomationVariable -Name 'AZURE_CLIENT_ID'
$clientSecret = Get-AutomationVariable -Name 'AZURE_CLIENT_SECRET'
$subscriptionId = Get-AutomationVariable -Name 'AZURE_SUBSCRIPTION_ID'
$protectedRGs = Get-AutomationVariable -Name 'PROTECTED_RESOURCE_GROUPS'

$secureSecret = ConvertTo-SecureString -String $clientSecret -AsPlainText -Force
$credential = New-Object System.Management.Automation.PSCredential ($clientId, $secureSecret)

Connect-AzAccount -ServicePrincipal -Credential $credential -TenantId $tenantId -SubscriptionId $subscriptionId

# Data atual
$currentDate = Get-Date -Format "yyyy-MM-dd"
Write-Output "Data atual: $currentDate"

# Converter lista de RGs protegidos
$protectedResourceGroups = $protectedRGs -split ","

# Obter todos os recursos
$resources = Get-AzResource

foreach ($resource in $resources) {
    $expireOn = $resource.Tags["ExpireOn"]
    $resourceOwner = $resource.Tags["ResourceOwner"]
    
    # Verificar se o resource group está protegido
    $isProtected = $protectedResourceGroups -contains $resource.ResourceGroupName
    
    if ($isProtected) {
        Write-Output "Recurso protegido (RG protegido): $($resource.Name) no RG: $($resource.ResourceGroupName)"
        continue
    }
    
    # Verificar se tem tags obrigatórias
    if ([string]::IsNullOrEmpty($resourceOwner) -or [string]::IsNullOrEmpty($expireOn)) {
        if ($action -eq "delete") {
            Write-Output "Excluindo recurso sem tags obrigatórias: $($resource.Name)"
            Remove-AzResource -ResourceId $resource.ResourceId -Force
        } else {
            Write-Output "Recurso que seria excluído (sem tags): $($resource.Name)"
        }
    }
    # Verificar se a tag ExpireOn está vencida
    elseif ($expireOn -lt $currentDate) {
        if ($action -eq "delete") {
            Write-Output "Excluindo recurso expirado: $($resource.Name) (Expirou em: $expireOn)"
            Remove-AzResource -ResourceId $resource.ResourceId -Force
        } else {
            Write-Output "Recurso que seria excluído (expirado): $($resource.Name) (Expirou em: $expireOn)"
        }
    }
    else {
        Write-Output "Recurso válido: $($resource.Name) (Expira em: $expireOn)"
    }
}
EOF

az automation runbook create \
    --automation-account-name "$AUTOMATION_ACCOUNT_NAME" \
    --resource-group "$RESOURCE_GROUP_NAME" \
    --name "CleanupExpiredTagsRunbook" \
    --type "PowerShell" \
    --description "Runbook para limpar recursos com tags expiradas"

az automation runbook replace-content \
    --automation-account-name "$AUTOMATION_ACCOUNT_NAME" \
    --resource-group "$RESOURCE_GROUP_NAME" \
    --name "CleanupExpiredTagsRunbook" \
    --content-path "/tmp/cleanup-expired-tags-runbook.ps1"

az automation runbook publish \
    --automation-account-name "$AUTOMATION_ACCOUNT_NAME" \
    --resource-group "$RESOURCE_GROUP_NAME" \
    --name "CleanupExpiredTagsRunbook"

log "Runbook de limpeza por tags criado com sucesso!"

# =============================================================================
# CRIAR RUNBOOK DE REMOÇÃO DE LOCKS
# =============================================================================
log "Criando runbook de remoção de locks..."

cat > /tmp/remove-subscription-lock-runbook.ps1 << 'EOF'
param()

Import-Module Az.Accounts
Import-Module Az.Resources

# Obter credenciais
$tenantId = Get-AutomationVariable -Name 'AZURE_TENANT_ID'
$clientId = Get-AutomationVariable -Name 'AZURE_CLIENT_ID'
$clientSecret = Get-AutomationVariable -Name 'AZURE_CLIENT_SECRET'
$subscriptionId = Get-AutomationVariable -Name 'AZURE_SUBSCRIPTION_ID'
$lockRemovalDay = Get-AutomationVariable -Name 'LOCK_REMOVAL_DAY'

$secureSecret = ConvertTo-SecureString -String $clientSecret -AsPlainText -Force
$credential = New-Object System.Management.Automation.PSCredential ($clientId, $secureSecret)

Connect-AzAccount -ServicePrincipal -Credential $credential -TenantId $tenantId -SubscriptionId $subscriptionId

# Verificar se é o dia configurado para remoção
$currentDay = (Get-Date).Day
Write-Output "Dia atual: $currentDay, Dia configurado para remoção: $lockRemovalDay"

if ($currentDay -eq [int]$lockRemovalDay) {
    Write-Output "É o dia configurado para remoção de locks!"
    
    # Procurar pelo lock de budget
    $locks = Get-AzResourceLock -Scope "/subscriptions/$subscriptionId"
    $budgetLock = $locks | Where-Object { $_.Name -eq "Prevent-Spending-BudgetControl" }
    
    if ($budgetLock) {
        Write-Output "Lock de budget encontrado. Removendo..."
        Remove-AzResourceLock -LockId $budgetLock.LockId -Force
        Write-Output "Lock removido com sucesso!"
    } else {
        Write-Output "Lock de budget não encontrado."
    }
} else {
    Write-Output "Não é o dia configurado para remoção de locks."
}
EOF

az automation runbook create \
    --automation-account-name "$AUTOMATION_ACCOUNT_NAME" \
    --resource-group "$RESOURCE_GROUP_NAME" \
    --name "RemoveSubscriptionLockRunbook" \
    --type "PowerShell" \
    --description "Runbook para remover locks da subscription no dia configurado"

az automation runbook replace-content \
    --automation-account-name "$AUTOMATION_ACCOUNT_NAME" \
    --resource-group "$RESOURCE_GROUP_NAME" \
    --name "RemoveSubscriptionLockRunbook" \
    --content-path "/tmp/remove-subscription-lock-runbook.ps1"

az automation runbook publish \
    --automation-account-name "$AUTOMATION_ACCOUNT_NAME" \
    --resource-group "$RESOURCE_GROUP_NAME" \
    --name "RemoveSubscriptionLockRunbook"

log "Runbook de remoção de locks criado com sucesso!"

# =============================================================================
# CRIAR VARIÁVEIS DE AUTOMAÇÃO
# =============================================================================
log "Criando variáveis de automação..."

# Criar variáveis necessárias
az automation variable create \
    --automation-account-name "$AUTOMATION_ACCOUNT_NAME" \
    --resource-group "$RESOURCE_GROUP_NAME" \
    --name "AZURE_TENANT_ID" \
    --value "$AZURE_TENANT_ID"

az automation variable create \
    --automation-account-name "$AUTOMATION_ACCOUNT_NAME" \
    --resource-group "$RESOURCE_GROUP_NAME" \
    --name "AZURE_CLIENT_ID" \
    --value "$AZURE_CLIENT_ID"

az automation variable create \
    --automation-account-name "$AUTOMATION_ACCOUNT_NAME" \
    --resource-group "$RESOURCE_GROUP_NAME" \
    --name "AZURE_CLIENT_SECRET" \
    --value "$AZURE_CLIENT_SECRET" \
    --encrypted

az automation variable create \
    --automation-account-name "$AUTOMATION_ACCOUNT_NAME" \
    --resource-group "$RESOURCE_GROUP_NAME" \
    --name "AZURE_SUBSCRIPTION_ID" \
    --value "$AZURE_SUBSCRIPTION_ID"

az automation variable create \
    --automation-account-name "$AUTOMATION_ACCOUNT_NAME" \
    --resource-group "$RESOURCE_GROUP_NAME" \
    --name "SHUTDOWN_TIME" \
    --value "$SHUTDOWN_TIME"

az automation variable create \
    --automation-account-name "$AUTOMATION_ACCOUNT_NAME" \
    --resource-group "$RESOURCE_GROUP_NAME" \
    --name "TIMEZONE" \
    --value "$TIMEZONE"

az automation variable create \
    --automation-account-name "$AUTOMATION_ACCOUNT_NAME" \
    --resource-group "$RESOURCE_GROUP_NAME" \
    --name "LOCK_REMOVAL_DAY" \
    --value "$LOCK_REMOVAL_DAY"

az automation variable create \
    --automation-account-name "$AUTOMATION_ACCOUNT_NAME" \
    --resource-group "$RESOURCE_GROUP_NAME" \
    --name "PROTECTED_RESOURCE_GROUPS" \
    --value "$PROTECTED_RESOURCE_GROUPS"

log "Variáveis de automação criadas com sucesso!"

# =============================================================================
# CRIAR SCHEDULES PARA AUTOMAÇÕES
# =============================================================================
log "Criando agendamentos para automações..."

# Schedule para shutdown diário às 19:00
az automation schedule create \
    --automation-account-name "$AUTOMATION_ACCOUNT_NAME" \
    --resource-group "$RESOURCE_GROUP_NAME" \
    --name "DailyShutdownSchedule" \
    --frequency "Day" \
    --interval 1 \
    --start-time "$(date -d 'today 19:00' -u +%Y-%m-%dT%H:%M:%S.000Z)"

# Schedule para limpeza de tags diário às 20:00
az automation schedule create \
    --automation-account-name "$AUTOMATION_ACCOUNT_NAME" \
    --resource-group "$RESOURCE_GROUP_NAME" \
    --name "DailyTagCleanupSchedule" \
    --frequency "Day" \
    --interval 1 \
    --start-time "$(date -d 'today 20:00' -u +%Y-%m-%dT%H:%M:%S.000Z)"

# Schedule para remoção de locks mensal
az automation schedule create \
    --automation-account-name "$AUTOMATION_ACCOUNT_NAME" \
    --resource-group "$RESOURCE_GROUP_NAME" \
    --name "MonthlyLockRemovalSchedule" \
    --frequency "Month" \
    --interval 1 \
    --start-time "$(date -d "$(date +%Y-%m-${LOCK_REMOVAL_DAY}) 09:00" -u +%Y-%m-%dT%H:%M:%S.000Z)"

log "Agendamentos criados com sucesso!"

# =============================================================================
# ASSOCIAR RUNBOOKS AOS SCHEDULES
# =============================================================================
log "Associando runbooks aos agendamentos..."

# Associar shutdown runbook
az automation job-schedule create \
    --automation-account-name "$AUTOMATION_ACCOUNT_NAME" \
    --resource-group "$RESOURCE_GROUP_NAME" \
    --runbook-name "ShutdownResourcesRunbook" \
    --schedule-name "DailyShutdownSchedule" \
    --parameters action="$DEFAULT_ACTION_EXPIRED_RESOURCES"

# Associar tag cleanup runbook
az automation job-schedule create \
    --automation-account-name "$AUTOMATION_ACCOUNT_NAME" \
    --resource-group "$RESOURCE_GROUP_NAME" \
    --runbook-name "CleanupExpiredTagsRunbook" \
    --schedule-name "DailyTagCleanupSchedule" \
    --parameters action="$DEFAULT_ACTION_EXPIRED_RESOURCES"

# Associar lock removal runbook
az automation job-schedule create \
    --automation-account-name "$AUTOMATION_ACCOUNT_NAME" \
    --resource-group "$RESOURCE_GROUP_NAME" \
    --runbook-name "RemoveSubscriptionLockRunbook" \
    --schedule-name "MonthlyLockRemovalSchedule"

log "Runbooks associados aos agendamentos com sucesso!"

# =============================================================================
# RESUMO
# =============================================================================
log "=========================================="
log "AUTOMAÇÕES CONFIGURADAS COM SUCESSO! 🤖"
log "=========================================="
log ""
log "Runbooks criados:"
log "  ✅ ShutdownResourcesRunbook - Desliga recursos às $SHUTDOWN_TIME"
log "  ✅ CleanupExpiredTagsRunbook - Limpa recursos com tags expiradas às 20:00"
log "  ✅ RemoveSubscriptionLockRunbook - Remove locks no dia $LOCK_REMOVAL_DAY"
log ""
log "Agendamentos:"
log "  🕐 Shutdown diário às $SHUTDOWN_TIME"
log "  🕐 Limpeza de tags diária às 20:00"
log "  🕐 Remoção de locks no dia $LOCK_REMOVAL_DAY de cada mês"
log ""
log "Ação padrão: $DEFAULT_ACTION_EXPIRED_RESOURCES (show/delete)"
log ""
log "Para testar manualmente:"
log "  az automation runbook start --automation-account-name $AUTOMATION_ACCOUNT_NAME --resource-group $RESOURCE_GROUP_NAME --name ShutdownResourcesRunbook"
log ""

log "Automações configuradas! 🎉"

