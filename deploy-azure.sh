#!/bin/bash

# BOLT Dashboard - Script de Deploy para Azure
# Este script automatiza o deploy completo do dashboard no Azure

set -e

echo "🚀 BOLT Dashboard - Deploy Automático para Azure"
echo "=================================================="

# Verificar se Azure CLI está instalado
if ! command -v az &> /dev/null; then
    echo "❌ Azure CLI não encontrado. Instale com: curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash"
    exit 1
fi

# Verificar login no Azure
if ! az account show &> /dev/null; then
    echo "❌ Não logado no Azure. Execute: az login"
    exit 1
fi

# Configurações
RESOURCE_GROUP="bolt-dashboard-rg"
LOCATION="eastus"
APP_NAME="bolt-dashboard"
STORAGE_ACCOUNT="${APP_NAME}storage$(date +%s)"
FUNCTION_APP="${APP_NAME}-api"

echo "📋 Configurações:"
echo "   Resource Group: $RESOURCE_GROUP"
echo "   Location: $LOCATION"
echo "   App Name: $APP_NAME"
echo "   Storage Account: $STORAGE_ACCOUNT"
echo "   Function App: $FUNCTION_APP"
echo ""

# Criar Resource Group
echo "🔧 Criando Resource Group..."
az group create --name $RESOURCE_GROUP --location $LOCATION

# Registrar providers necessários
echo "🔧 Registrando providers do Azure..."
az provider register --namespace Microsoft.Web
az provider register --namespace Microsoft.Storage

# Criar Storage Account
echo "🔧 Criando Storage Account..."
az storage account create \
    --name $STORAGE_ACCOUNT \
    --resource-group $RESOURCE_GROUP \
    --location $LOCATION \
    --sku Standard_LRS \
    --kind StorageV2

# Habilitar hosting estático
echo "🔧 Habilitando hosting estático..."
az storage blob service-properties update \
    --account-name $STORAGE_ACCOUNT \
    --static-website \
    --index-document index.html \
    --404-document index.html

# Criar Function App
echo "🔧 Criando Azure Function App..."
az functionapp create \
    --resource-group $RESOURCE_GROUP \
    --consumption-plan-location $LOCATION \
    --runtime python \
    --runtime-version 3.11 \
    --functions-version 4 \
    --name $FUNCTION_APP \
    --storage-account $STORAGE_ACCOUNT \
    --os-type Linux

# Build do frontend
echo "🔧 Fazendo build do frontend..."
cd azure-dashboard-frontend
npm install
npm run build

# Upload do frontend para Storage
echo "🔧 Fazendo upload do frontend..."
az storage blob upload-batch \
    --account-name $STORAGE_ACCOUNT \
    --destination '$web' \
    --source dist/

# Deploy do backend
echo "🔧 Fazendo deploy do backend..."
cd ../azure-dashboard-backend
zip -r function-app.zip . -x "*.git*" "*__pycache__*" "*.pyc"

az functionapp deployment source config-zip \
    --resource-group $RESOURCE_GROUP \
    --name $FUNCTION_APP \
    --src function-app.zip

# Obter URLs
FRONTEND_URL=$(az storage account show --name $STORAGE_ACCOUNT --resource-group $RESOURCE_GROUP --query "primaryEndpoints.web" --output tsv)
BACKEND_URL=$(az functionapp show --name $FUNCTION_APP --resource-group $RESOURCE_GROUP --query "defaultHostName" --output tsv)

echo ""
echo "✅ Deploy concluído com sucesso!"
echo "================================"
echo "🌐 Frontend URL: $FRONTEND_URL"
echo "🔧 Backend URL: https://$BACKEND_URL"
echo ""
echo "📝 Próximos passos:"
echo "1. Configure as variáveis de ambiente no Function App"
echo "2. Atualize a URL do backend no frontend"
echo "3. Teste o sistema completo"
echo ""
echo "🎉 BOLT Dashboard está pronto para uso!"

