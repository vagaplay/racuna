#!/bin/bash

# Script de Deploy Automatizado para BOLT Dashboard
# Este script faz o deploy completo da aplicação no Azure

set -e  # Parar em caso de erro

echo "🚀 Iniciando deploy do BOLT Dashboard..."

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Função para log colorido
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[WARNING] $1${NC}"
}

error() {
    echo -e "${RED}[ERROR] $1${NC}"
    exit 1
}

# Verificar dependências
check_dependencies() {
    log "Verificando dependências..."
    
    if ! command -v az &> /dev/null; then
        error "Azure CLI não encontrado. Instale: https://docs.microsoft.com/en-us/cli/azure/install-azure-cli"
    fi
    
    if ! command -v terraform &> /dev/null; then
        error "Terraform não encontrado. Instale: https://www.terraform.io/downloads.html"
    fi
    
    if ! command -v node &> /dev/null; then
        error "Node.js não encontrado. Instale: https://nodejs.org/"
    fi
    
    if ! command -v python3 &> /dev/null; then
        error "Python 3 não encontrado."
    fi
    
    log "✅ Todas as dependências encontradas"
}

# Login no Azure
azure_login() {
    log "Verificando login no Azure..."
    
    if ! az account show &> /dev/null; then
        log "Fazendo login no Azure..."
        az login
    fi
    
    # Verificar subscription
    SUBSCRIPTION=$(az account show --query id -o tsv)
    log "✅ Conectado à subscription: $SUBSCRIPTION"
}

# Preparar infraestrutura com Terraform
deploy_infrastructure() {
    log "Preparando infraestrutura com Terraform..."
    
    cd terraform
    
    # Verificar se terraform.tfvars existe
    if [ ! -f "terraform.tfvars" ]; then
        warn "Arquivo terraform.tfvars não encontrado!"
        echo "Copie terraform.tfvars.example para terraform.tfvars e configure suas variáveis."
        echo "cp terraform.tfvars.example terraform.tfvars"
        error "Configure terraform.tfvars antes de continuar"
    fi
    
    # Inicializar Terraform
    log "Inicializando Terraform..."
    terraform init
    
    # Planejar deployment
    log "Planejando deployment..."
    terraform plan -out=tfplan
    
    # Aplicar mudanças
    log "Aplicando infraestrutura..."
    terraform apply tfplan
    
    # Obter outputs
    BACKEND_URL=$(terraform output -raw backend_url)
    FRONTEND_URL=$(terraform output -raw frontend_url)
    RESOURCE_GROUP=$(terraform output -raw resource_group_name)
    
    log "✅ Infraestrutura criada:"
    log "   Backend URL: $BACKEND_URL"
    log "   Frontend URL: $FRONTEND_URL"
    log "   Resource Group: $RESOURCE_GROUP"
    
    cd ..
}

# Build do frontend
build_frontend() {
    log "Fazendo build do frontend..."
    
    cd azure-dashboard-frontend
    
    # Instalar dependências
    log "Instalando dependências do frontend..."
    npm install
    
    # Configurar variáveis de ambiente para produção
    cat > .env.production << EOF
VITE_API_BASE_URL=$BACKEND_URL
VITE_ENVIRONMENT=production
EOF
    
    # Build para produção
    log "Executando build de produção..."
    npm run build
    
    log "✅ Frontend buildado com sucesso"
    cd ..
}

# Deploy do backend
deploy_backend() {
    log "Fazendo deploy do backend..."
    
    cd azure-dashboard-backend
    
    # Criar arquivo de requirements se não existir
    if [ ! -f "requirements.txt" ]; then
        log "Gerando requirements.txt..."
        pip freeze > requirements.txt
    fi
    
    # Criar arquivo de startup para Azure
    cat > startup.sh << 'EOF'
#!/bin/bash
cd /home/site/wwwroot
python -m pip install --upgrade pip
pip install -r requirements.txt
python src/main.py
EOF
    
    # Deploy usando Azure CLI
    log "Fazendo upload do código do backend..."
    az webapp up --name $(terraform -chdir=../terraform output -raw backend_app_name) \
                 --resource-group $(terraform -chdir=../terraform output -raw resource_group_name) \
                 --runtime "PYTHON:3.11"
    
    log "✅ Backend deployado com sucesso"
    cd ..
}

# Deploy do frontend
deploy_frontend() {
    log "Fazendo deploy do frontend..."
    
    cd azure-dashboard-frontend
    
    # Deploy para Static Web App usando SWA CLI
    if command -v swa &> /dev/null; then
        log "Usando SWA CLI para deploy..."
        swa deploy ./dist --env production
    else
        warn "SWA CLI não encontrado. Deploy manual necessário."
        log "1. Acesse: https://portal.azure.com"
        log "2. Vá para o Static Web App criado"
        log "3. Configure GitHub Actions ou faça upload manual da pasta 'dist'"
    fi
    
    cd ..
}

# Deploy das Azure Functions
deploy_functions() {
    log "Fazendo deploy das Azure Functions..."
    
    cd azure-functions-project
    
    # Instalar Azure Functions Core Tools se necessário
    if ! command -v func &> /dev/null; then
        warn "Azure Functions Core Tools não encontrado"
        log "Instale: npm install -g azure-functions-core-tools@4 --unsafe-perm true"
        return
    fi
    
    # Deploy das functions
    FUNCTION_APP_NAME=$(terraform -chdir=../terraform output -raw function_app_name)
    func azure functionapp publish $FUNCTION_APP_NAME --python
    
    log "✅ Azure Functions deployadas com sucesso"
    cd ..
}

# Configurar domínio customizado (opcional)
configure_custom_domain() {
    if [ ! -z "$CUSTOM_DOMAIN" ]; then
        log "Configurando domínio customizado: $CUSTOM_DOMAIN"
        
        # Configurar domínio no Static Web App
        az staticwebapp hostname set \
            --name $(terraform -chdir=terraform output -raw frontend_app_name) \
            --resource-group $(terraform -chdir=terraform output -raw resource_group_name) \
            --hostname $CUSTOM_DOMAIN
        
        log "✅ Domínio customizado configurado"
    fi
}

# Verificar saúde da aplicação
health_check() {
    log "Verificando saúde da aplicação..."
    
    # Aguardar um pouco para os serviços iniciarem
    sleep 30
    
    # Verificar backend
    if curl -f -s "$BACKEND_URL/api/health" > /dev/null; then
        log "✅ Backend está respondendo"
    else
        warn "❌ Backend não está respondendo"
    fi
    
    # Verificar frontend
    if curl -f -s "$FRONTEND_URL" > /dev/null; then
        log "✅ Frontend está acessível"
    else
        warn "❌ Frontend não está acessível"
    fi
}

# Função principal
main() {
    log "🚀 Iniciando deploy completo do BOLT Dashboard"
    
    check_dependencies
    azure_login
    deploy_infrastructure
    build_frontend
    deploy_backend
    deploy_frontend
    deploy_functions
    configure_custom_domain
    health_check
    
    log "🎉 Deploy concluído com sucesso!"
    log ""
    log "📊 URLs da aplicação:"
    log "   Frontend: $FRONTEND_URL"
    log "   Backend:  $BACKEND_URL"
    log ""
    log "🔧 Próximos passos:"
    log "   1. Configure as credenciais Azure na aplicação"
    log "   2. Teste todas as funcionalidades"
    log "   3. Configure alertas e monitoramento"
    log "   4. Configure backup automático"
}

# Executar função principal
main "$@"

