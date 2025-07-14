#!/bin/bash

# Script de inicialização para o projeto BOLT
# Este script configura o ambiente Terraform e executa o deployment inicial

set -e

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Função para logging
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Verificar se o Azure CLI está instalado
check_azure_cli() {
    if ! command -v az &> /dev/null; then
        error "Azure CLI não está instalado. Por favor, instale o Azure CLI primeiro."
        exit 1
    fi
    
    # Verificar se está logado
    if ! az account show &> /dev/null; then
        error "Você não está logado no Azure CLI. Execute 'az login' primeiro."
        exit 1
    fi
    
    success "Azure CLI está configurado corretamente"
}

# Verificar se o Terraform está instalado
check_terraform() {
    if ! command -v terraform &> /dev/null; then
        error "Terraform não está instalado. Por favor, instale o Terraform primeiro."
        exit 1
    fi
    
    success "Terraform está instalado"
}

# Criar backend do Terraform
create_terraform_backend() {
    log "Criando backend do Terraform..."
    
    local resource_group="terraform-state-rg"
    local storage_account="terraformstatebolt$(date +%s | tail -c 6)"
    local container_name="tfstate"
    local location="East US"
    
    # Criar resource group para o state
    az group create --name $resource_group --location "$location" --output none
    
    # Criar storage account
    az storage account create \
        --resource-group $resource_group \
        --name $storage_account \
        --sku Standard_LRS \
        --encryption-services blob \
        --output none
    
    # Criar container
    az storage container create \
        --name $container_name \
        --account-name $storage_account \
        --output none
    
    success "Backend do Terraform criado com sucesso"
    log "Resource Group: $resource_group"
    log "Storage Account: $storage_account"
    log "Container: $container_name"
    
    # Atualizar o arquivo de configuração do backend
    cat > backend.tf << EOF
terraform {
  backend "azurerm" {
    resource_group_name  = "$resource_group"
    storage_account_name = "$storage_account"
    container_name       = "$container_name"
    key                  = "bolt.tfstate"
  }
}
EOF
    
    success "Arquivo backend.tf criado"
}

# Configurar variáveis do Terraform
setup_terraform_vars() {
    log "Configurando variáveis do Terraform..."
    
    if [ ! -f "terraform.tfvars" ]; then
        if [ -f "terraform.tfvars.example" ]; then
            cp terraform.tfvars.example terraform.tfvars
            warning "Arquivo terraform.tfvars criado a partir do exemplo"
            warning "Por favor, edite o arquivo terraform.tfvars com suas configurações"
            return 1
        else
            error "Arquivo terraform.tfvars.example não encontrado"
            return 1
        fi
    fi
    
    success "Arquivo terraform.tfvars já existe"
    return 0
}

# Executar Terraform
run_terraform() {
    local environment=${1:-dev}
    
    log "Executando Terraform para o ambiente: $environment"
    
    # Inicializar Terraform
    log "Inicializando Terraform..."
    terraform init
    
    # Validar configuração
    log "Validando configuração..."
    terraform validate
    
    # Planejar deployment
    log "Criando plano de deployment..."
    terraform plan -var-file="environments/${environment}.tfvars" -out=tfplan
    
    # Confirmar execução
    echo
    warning "Você está prestes a executar o deployment para o ambiente: $environment"
    read -p "Deseja continuar? (y/N): " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        log "Aplicando configuração..."
        terraform apply tfplan
        success "Deployment concluído com sucesso!"
        
        # Mostrar outputs
        log "Outputs do deployment:"
        terraform output
    else
        warning "Deployment cancelado pelo usuário"
    fi
}

# Função principal
main() {
    log "Iniciando setup do projeto BOLT"
    
    # Verificar pré-requisitos
    check_azure_cli
    check_terraform
    
    # Mudar para o diretório do Terraform
    cd "$(dirname "$0")"
    
    # Verificar se já existe backend
    if [ ! -f "backend.tf" ]; then
        create_terraform_backend
    else
        log "Backend do Terraform já existe"
    fi
    
    # Configurar variáveis
    if ! setup_terraform_vars; then
        error "Por favor, configure o arquivo terraform.tfvars antes de continuar"
        exit 1
    fi
    
    # Executar Terraform
    local environment=${1:-dev}
    run_terraform $environment
}

# Verificar argumentos
if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    echo "Uso: $0 [ambiente]"
    echo
    echo "Ambientes disponíveis:"
    echo "  dev      - Ambiente de desenvolvimento (padrão)"
    echo "  staging  - Ambiente de staging"
    echo "  prod     - Ambiente de produção"
    echo
    echo "Exemplos:"
    echo "  $0           # Deploy para dev"
    echo "  $0 dev       # Deploy para dev"
    echo "  $0 prod      # Deploy para produção"
    exit 0
fi

# Executar função principal
main "$@"

