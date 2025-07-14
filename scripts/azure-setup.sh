#!/bin/bash

# =============================================================================
# BOLT DASHBOARD - SETUP INFRAESTRUTURA AZURE
# =============================================================================
# Este script cria toda a infraestrutura Azure necessária para o projeto

set -e  # Parar em caso de erro

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Função para log
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
    log "Carregando configurações do arquivo .env..."
    set -o allexport
    source .env
    set +o allexport
else
    error "Arquivo .env não encontrado. Copie .env.template para .env e configure suas credenciais."
fi

# Verificar credenciais obrigatórias
if [ -z "$AZURE_SUBSCRIPTION_ID" ] || [ -z "$AZURE_TENANT_ID" ] || [ -z "$AZURE_CLIENT_ID" ] || [ -z "$AZURE_CLIENT_SECRET" ]; then
    error "Credenciais Azure não configuradas no arquivo .env"
fi

# Configurações padrão
RESOURCE_GROUP_NAME=${RESOURCE_GROUP_NAME:-"rg-bolt-dashboard"}
CONTAINER_REGISTRY_NAME=${CONTAINER_REGISTRY_NAME:-"boltdashboardacr"}
APP_SERVICE_NAME=${APP_SERVICE_NAME:-"app-bolt-dashboard"}
DEFAULT_AZURE_REGION=${DEFAULT_AZURE_REGION:-"Brazil South"}
KEY_VAULT_NAME=${KEY_VAULT_NAME:-"kv-bolt-dashboard"}
STORAGE_ACCOUNT_NAME=${STORAGE_ACCOUNT_NAME:-"stboltdashboard"}

log "Configurações:"
log "  Resource Group: $RESOURCE_GROUP_NAME"
log "  Container Registry: $CONTAINER_REGISTRY_NAME"
log "  App Service: $APP_SERVICE_NAME"
log "  Região: $DEFAULT_AZURE_REGION"

# =============================================================================
# LOGIN NO AZURE
# =============================================================================
log "Fazendo login no Azure..."

# Login com Service Principal
az login --service-principal \
    --username "$AZURE_CLIENT_ID" \
    --password "$AZURE_CLIENT_SECRET" \
    --tenant "$AZURE_TENANT_ID" > /dev/null

# Definir subscription
az account set --subscription "$AZURE_SUBSCRIPTION_ID"

log "Login realizado com sucesso!"
log "Subscription ativa: $(az account show --query name -o tsv)"

# =============================================================================
# CRIAR RESOURCE GROUP
# =============================================================================
log "Criando Resource Group: $RESOURCE_GROUP_NAME..."

if az group show --name "$RESOURCE_GROUP_NAME" > /dev/null 2>&1; then
    warn "Resource Group $RESOURCE_GROUP_NAME já existe"
else
    az group create \
        --name "$RESOURCE_GROUP_NAME" \
        --location "$DEFAULT_AZURE_REGION" \
        --tags "Project=BoltDashboard" "Environment=Production" "CreatedBy=AutomationScript"
    log "Resource Group criado com sucesso!"
fi

# =============================================================================
# CRIAR CONTAINER REGISTRY
# =============================================================================
log "Criando Container Registry: $CONTAINER_REGISTRY_NAME..."

if az acr show --name "$CONTAINER_REGISTRY_NAME" --resource-group "$RESOURCE_GROUP_NAME" > /dev/null 2>&1; then
    warn "Container Registry $CONTAINER_REGISTRY_NAME já existe"
else
    az acr create \
        --name "$CONTAINER_REGISTRY_NAME" \
        --resource-group "$RESOURCE_GROUP_NAME" \
        --sku Basic \
        --admin-enabled true \
        --tags "Project=BoltDashboard"
    log "Container Registry criado com sucesso!"
fi

# =============================================================================
# CRIAR KEY VAULT
# =============================================================================
log "Criando Key Vault: $KEY_VAULT_NAME..."

# Gerar nome único para Key Vault (máximo 24 caracteres)
UNIQUE_SUFFIX=$(echo $AZURE_SUBSCRIPTION_ID | tail -c 5)
KEY_VAULT_NAME_UNIQUE="${KEY_VAULT_NAME}-${UNIQUE_SUFFIX}"

if az keyvault show --name "$KEY_VAULT_NAME_UNIQUE" > /dev/null 2>&1; then
    warn "Key Vault $KEY_VAULT_NAME_UNIQUE já existe"
else
    az keyvault create \
        --name "$KEY_VAULT_NAME_UNIQUE" \
        --resource-group "$RESOURCE_GROUP_NAME" \
        --location "$DEFAULT_AZURE_REGION" \
        --sku standard \
        --tags "Project=BoltDashboard"
    log "Key Vault criado com sucesso!"
fi

# Adicionar credenciais ao Key Vault
log "Adicionando credenciais ao Key Vault..."
az keyvault secret set --vault-name "$KEY_VAULT_NAME_UNIQUE" --name "AZURE-TENANT-ID" --value "$AZURE_TENANT_ID" > /dev/null
az keyvault secret set --vault-name "$KEY_VAULT_NAME_UNIQUE" --name "AZURE-CLIENT-ID" --value "$AZURE_CLIENT_ID" > /dev/null
az keyvault secret set --vault-name "$KEY_VAULT_NAME_UNIQUE" --name "AZURE-CLIENT-SECRET" --value "$AZURE_CLIENT_SECRET" > /dev/null
az keyvault secret set --vault-name "$KEY_VAULT_NAME_UNIQUE" --name "AZURE-SUBSCRIPTION-ID" --value "$AZURE_SUBSCRIPTION_ID" > /dev/null
az keyvault secret set --vault-name "$KEY_VAULT_NAME_UNIQUE" --name "JWT-SECRET-KEY" --value "$JWT_SECRET_KEY" > /dev/null

log "Credenciais adicionadas ao Key Vault!"

# =============================================================================
# CRIAR STORAGE ACCOUNT
# =============================================================================
log "Criando Storage Account: $STORAGE_ACCOUNT_NAME..."

# Gerar nome único para Storage Account (máximo 24 caracteres, apenas letras e números)
STORAGE_UNIQUE=$(echo "${STORAGE_ACCOUNT_NAME}${UNIQUE_SUFFIX}" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9]//g' | cut -c1-24)

if az storage account show --name "$STORAGE_UNIQUE" --resource-group "$RESOURCE_GROUP_NAME" > /dev/null 2>&1; then
    warn "Storage Account $STORAGE_UNIQUE já existe"
else
    az storage account create \
        --name "$STORAGE_UNIQUE" \
        --resource-group "$RESOURCE_GROUP_NAME" \
        --location "$DEFAULT_AZURE_REGION" \
        --sku Standard_LRS \
        --kind StorageV2 \
        --tags "Project=BoltDashboard"
    log "Storage Account criado com sucesso!"
fi

# Criar File Share para dados persistentes
log "Criando File Share para dados persistentes..."
STORAGE_KEY=$(az storage account keys list --resource-group "$RESOURCE_GROUP_NAME" --account-name "$STORAGE_UNIQUE" --query '[0].value' -o tsv)

az storage share create \
    --name "bolt-dashboard-data" \
    --account-name "$STORAGE_UNIQUE" \
    --account-key "$STORAGE_KEY" > /dev/null

log "File Share criado com sucesso!"

# =============================================================================
# CRIAR CONTAINER INSTANCE (OPÇÃO ECONÔMICA)
# =============================================================================
log "Criando Container Instance para deploy econômico..."

# Obter credenciais do Container Registry
ACR_USERNAME=$(az acr credential show --name "$CONTAINER_REGISTRY_NAME" --query username -o tsv)
ACR_PASSWORD=$(az acr credential show --name "$CONTAINER_REGISTRY_NAME" --query passwords[0].value -o tsv)

# Criar Container Instance (será usado depois do build da imagem)
cat > /tmp/container-instance.yaml << EOF
apiVersion: 2019-12-01
location: $DEFAULT_AZURE_REGION
name: bolt-dashboard-ci
properties:
  containers:
  - name: bolt-dashboard
    properties:
      image: ${CONTAINER_REGISTRY_NAME}.azurecr.io/bolt-dashboard:latest
      resources:
        requests:
          cpu: 1
          memoryInGb: 1.5
      ports:
      - port: 80
        protocol: TCP
      environmentVariables:
      - name: AZURE_TENANT_ID
        secureValue: $AZURE_TENANT_ID
      - name: AZURE_CLIENT_ID
        secureValue: $AZURE_CLIENT_ID
      - name: AZURE_CLIENT_SECRET
        secureValue: $AZURE_CLIENT_SECRET
      - name: AZURE_SUBSCRIPTION_ID
        secureValue: $AZURE_SUBSCRIPTION_ID
      - name: JWT_SECRET_KEY
        secureValue: $JWT_SECRET_KEY
      volumeMounts:
      - name: data-volume
        mountPath: /app/data
  imageRegistryCredentials:
  - server: ${CONTAINER_REGISTRY_NAME}.azurecr.io
    username: $ACR_USERNAME
    password: $ACR_PASSWORD
  ipAddress:
    type: Public
    ports:
    - protocol: TCP
      port: 80
    dnsNameLabel: bolt-dashboard-${UNIQUE_SUFFIX}
  osType: Linux
  volumes:
  - name: data-volume
    azureFile:
      shareName: bolt-dashboard-data
      storageAccountName: $STORAGE_UNIQUE
      storageAccountKey: $STORAGE_KEY
  restartPolicy: Always
tags:
  Project: BoltDashboard
  Environment: Production
EOF

log "Configuração do Container Instance salva em /tmp/container-instance.yaml"

# =============================================================================
# CRIAR AUTOMATION ACCOUNT (PARA LÓGICA BUDGETBASA)
# =============================================================================
log "Criando Automation Account para automações..."

AUTOMATION_ACCOUNT_NAME="aa-bolt-dashboard"

if az automation account show --name "$AUTOMATION_ACCOUNT_NAME" --resource-group "$RESOURCE_GROUP_NAME" > /dev/null 2>&1; then
    warn "Automation Account $AUTOMATION_ACCOUNT_NAME já existe"
else
    az automation account create \
        --name "$AUTOMATION_ACCOUNT_NAME" \
        --resource-group "$RESOURCE_GROUP_NAME" \
        --location "$DEFAULT_AZURE_REGION" \
        --sku Basic \
        --tags "Project=BoltDashboard"
    log "Automation Account criado com sucesso!"
fi

# =============================================================================
# RESUMO FINAL
# =============================================================================
log "=========================================="
log "INFRAESTRUTURA AZURE CRIADA COM SUCESSO!"
log "=========================================="
log ""
log "Recursos criados:"
log "  ✅ Resource Group: $RESOURCE_GROUP_NAME"
log "  ✅ Container Registry: $CONTAINER_REGISTRY_NAME"
log "  ✅ Key Vault: $KEY_VAULT_NAME_UNIQUE"
log "  ✅ Storage Account: $STORAGE_UNIQUE"
log "  ✅ File Share: bolt-dashboard-data"
log "  ✅ Automation Account: $AUTOMATION_ACCOUNT_NAME"
log ""
log "Próximos passos:"
log "  1. Execute: ./scripts/build-and-deploy.sh"
log "  2. Acesse: http://bolt-dashboard-${UNIQUE_SUFFIX}.brazilsouth.azurecontainer.io"
log ""
log "Custos estimados:"
log "  📊 Container Instance: ~R$ 36/mês"
log "  📦 Container Registry: ~R$ 25/mês"
log "  🔐 Key Vault: ~R$ 5/mês"
log "  💾 Storage Account: ~R$ 10/mês"
log "  🤖 Automation Account: ~R$ 5/mês"
log "  💰 TOTAL: ~R$ 81/mês"
log ""

# Salvar informações importantes
cat > azure-resources.txt << EOF
# BOLT DASHBOARD - RECURSOS AZURE CRIADOS
# Gerado em: $(date)

RESOURCE_GROUP_NAME=$RESOURCE_GROUP_NAME
CONTAINER_REGISTRY_NAME=$CONTAINER_REGISTRY_NAME
KEY_VAULT_NAME=$KEY_VAULT_NAME_UNIQUE
STORAGE_ACCOUNT_NAME=$STORAGE_UNIQUE
AUTOMATION_ACCOUNT_NAME=$AUTOMATION_ACCOUNT_NAME
CONTAINER_INSTANCE_URL=http://bolt-dashboard-${UNIQUE_SUFFIX}.brazilsouth.azurecontainer.io

# Credenciais Container Registry
ACR_USERNAME=$ACR_USERNAME
ACR_PASSWORD=$ACR_PASSWORD

# Para usar nos próximos scripts
export RESOURCE_GROUP_NAME=$RESOURCE_GROUP_NAME
export CONTAINER_REGISTRY_NAME=$CONTAINER_REGISTRY_NAME
export KEY_VAULT_NAME=$KEY_VAULT_NAME_UNIQUE
export STORAGE_ACCOUNT_NAME=$STORAGE_UNIQUE
EOF

log "Informações salvas em: azure-resources.txt"
log "Setup concluído com sucesso! 🎉"

