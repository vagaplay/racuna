#!/bin/bash

# =============================================================================
# BOLT DASHBOARD - BUILD E DEPLOY
# =============================================================================
# Este script faz build da imagem Docker e deploy para Azure Container Instance

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
    error "Arquivo .env não encontrado."
fi

# Carregar informações dos recursos Azure
if [ -f azure-resources.txt ]; then
    log "Carregando informações dos recursos Azure..."
    source azure-resources.txt
else
    error "Arquivo azure-resources.txt não encontrado. Execute primeiro: ./scripts/azure-setup.sh"
fi

# Verificar se Docker está disponível
if ! command -v docker &> /dev/null; then
    error "Docker não está instalado ou não está no PATH"
fi

# =============================================================================
# LOGIN NO AZURE E CONTAINER REGISTRY
# =============================================================================
log "Fazendo login no Azure..."

az login --service-principal \
    --username "$AZURE_CLIENT_ID" \
    --password "$AZURE_CLIENT_SECRET" \
    --tenant "$AZURE_TENANT_ID" > /dev/null

az account set --subscription "$AZURE_SUBSCRIPTION_ID"

log "Fazendo login no Container Registry..."
az acr login --name "$CONTAINER_REGISTRY_NAME"

# =============================================================================
# BUILD DA IMAGEM DOCKER
# =============================================================================
IMAGE_NAME="bolt-dashboard"
IMAGE_TAG="latest"
FULL_IMAGE_NAME="${CONTAINER_REGISTRY_NAME}.azurecr.io/${IMAGE_NAME}:${IMAGE_TAG}"

log "Iniciando build da imagem Docker..."
log "Imagem: $FULL_IMAGE_NAME"

# Build da imagem
docker build \
    --tag "$IMAGE_NAME:$IMAGE_TAG" \
    --tag "$FULL_IMAGE_NAME" \
    --build-arg BUILD_DATE="$(date -u +'%Y-%m-%dT%H:%M:%SZ')" \
    --build-arg VERSION="$IMAGE_TAG" \
    .

log "Build da imagem concluído com sucesso!"

# =============================================================================
# PUSH DA IMAGEM PARA CONTAINER REGISTRY
# =============================================================================
log "Fazendo push da imagem para Container Registry..."

docker push "$FULL_IMAGE_NAME"

log "Push da imagem concluído com sucesso!"

# =============================================================================
# DEPLOY PARA CONTAINER INSTANCE
# =============================================================================
log "Fazendo deploy para Azure Container Instance..."

# Verificar se Container Instance já existe
CONTAINER_INSTANCE_NAME="bolt-dashboard-ci"

if az container show --name "$CONTAINER_INSTANCE_NAME" --resource-group "$RESOURCE_GROUP_NAME" > /dev/null 2>&1; then
    log "Container Instance já existe. Atualizando..."
    
    # Deletar instância existente
    az container delete \
        --name "$CONTAINER_INSTANCE_NAME" \
        --resource-group "$RESOURCE_GROUP_NAME" \
        --yes
    
    log "Container Instance anterior removido."
fi

# Obter credenciais do Storage Account
STORAGE_KEY=$(az storage account keys list \
    --resource-group "$RESOURCE_GROUP_NAME" \
    --account-name "$STORAGE_ACCOUNT_NAME" \
    --query '[0].value' -o tsv)

# Criar novo Container Instance
log "Criando novo Container Instance..."

az container create \
    --resource-group "$RESOURCE_GROUP_NAME" \
    --name "$CONTAINER_INSTANCE_NAME" \
    --image "$FULL_IMAGE_NAME" \
    --registry-login-server "${CONTAINER_REGISTRY_NAME}.azurecr.io" \
    --registry-username "$ACR_USERNAME" \
    --registry-password "$ACR_PASSWORD" \
    --cpu 1 \
    --memory 1.5 \
    --ports 80 \
    --ip-address Public \
    --dns-name-label "bolt-dashboard-$(echo $AZURE_SUBSCRIPTION_ID | tail -c 5)" \
    --environment-variables \
        AZURE_TENANT_ID="$AZURE_TENANT_ID" \
        AZURE_CLIENT_ID="$AZURE_CLIENT_ID" \
        AZURE_SUBSCRIPTION_ID="$AZURE_SUBSCRIPTION_ID" \
        JWT_SECRET_KEY="$JWT_SECRET_KEY" \
        FLASK_ENV="production" \
        SHUTDOWN_TIME="$SHUTDOWN_TIME" \
        TIMEZONE="$TIMEZONE" \
        LOCK_REMOVAL_DAY="$LOCK_REMOVAL_DAY" \
    --secure-environment-variables \
        AZURE_CLIENT_SECRET="$AZURE_CLIENT_SECRET" \
    --azure-file-volume-account-name "$STORAGE_ACCOUNT_NAME" \
    --azure-file-volume-account-key "$STORAGE_KEY" \
    --azure-file-volume-share-name "bolt-dashboard-data" \
    --azure-file-volume-mount-path "/app/data" \
    --restart-policy Always

log "Container Instance criado com sucesso!"

# =============================================================================
# AGUARDAR INICIALIZAÇÃO
# =============================================================================
log "Aguardando inicialização da aplicação..."

# Obter URL da aplicação
CONTAINER_URL=$(az container show \
    --name "$CONTAINER_INSTANCE_NAME" \
    --resource-group "$RESOURCE_GROUP_NAME" \
    --query ipAddress.fqdn -o tsv)

if [ -n "$CONTAINER_URL" ]; then
    FULL_URL="http://$CONTAINER_URL"
    log "URL da aplicação: $FULL_URL"
    
    # Aguardar aplicação ficar disponível
    log "Testando disponibilidade da aplicação..."
    
    for i in {1..30}; do
        if curl -f "$FULL_URL/health" > /dev/null 2>&1; then
            log "Aplicação está respondendo!"
            break
        else
            log "Tentativa $i/30 - Aguardando aplicação inicializar..."
            sleep 10
        fi
    done
    
    # Teste final
    if curl -f "$FULL_URL/health" > /dev/null 2>&1; then
        log "✅ Deploy realizado com sucesso!"
        log "🌐 Acesse sua aplicação em: $FULL_URL"
        log "👤 Login: test@test.com"
        log "🔑 Senha: 123456"
    else
        warn "Deploy concluído, mas aplicação pode ainda estar inicializando."
        log "🌐 URL: $FULL_URL"
        log "⏳ Aguarde alguns minutos e tente acessar."
    fi
else
    error "Não foi possível obter URL do Container Instance"
fi

# =============================================================================
# LOGS E MONITORAMENTO
# =============================================================================
log "Para visualizar logs da aplicação:"
log "  az container logs --name $CONTAINER_INSTANCE_NAME --resource-group $RESOURCE_GROUP_NAME"
log ""
log "Para monitorar a aplicação:"
log "  az container show --name $CONTAINER_INSTANCE_NAME --resource-group $RESOURCE_GROUP_NAME"
log ""

# =============================================================================
# CONFIGURAR AUTOMAÇÕES (LÓGICA BUDGETBASA)
# =============================================================================
log "Configurando automações do projeto budgetbasa..."

# Criar runbook para shutdown de recursos
./scripts/setup-automation.sh

# =============================================================================
# RESUMO FINAL
# =============================================================================
log "=========================================="
log "DEPLOY CONCLUÍDO COM SUCESSO! 🎉"
log "=========================================="
log ""
log "📊 Aplicação: BOLT Dashboard"
log "🌐 URL: $FULL_URL"
log "👤 Login: test@test.com"
log "🔑 Senha: 123456"
log ""
log "📈 Recursos Azure:"
log "  • Container Instance: $CONTAINER_INSTANCE_NAME"
log "  • Container Registry: $CONTAINER_REGISTRY_NAME"
log "  • Storage Account: $STORAGE_ACCOUNT_NAME"
log "  • Key Vault: $KEY_VAULT_NAME"
log ""
log "💰 Custo estimado: ~R$ 81/mês"
log ""
log "🔧 Próximos passos:"
log "  1. Acesse a aplicação e teste todas as funcionalidades"
log "  2. Configure budgets e alertas"
log "  3. Teste automações de shutdown e cleanup"
log ""

# Salvar URL da aplicação
echo "BOLT_DASHBOARD_URL=$FULL_URL" >> azure-resources.txt

log "Deploy finalizado! 🚀"

