# BOLT Dashboard - Guia de Deployment

Este documento fornece instruções completas para fazer o deployment do BOLT Dashboard no Azure usando Terraform e Azure DevOps.

## 📋 Pré-requisitos

### Ferramentas Necessárias
- [Azure CLI](https://docs.microsoft.com/en-us/cli/azure/install-azure-cli) (versão 2.30+)
- [Terraform](https://www.terraform.io/downloads.html) (versão 1.0+)
- [Node.js](https://nodejs.org/) (versão 18+)
- [Python](https://www.python.org/) (versão 3.9+)
- Acesso ao Azure DevOps

### Permissões Azure
- Contributor ou Owner na subscription Azure
- Permissões para criar Service Principals
- Acesso ao Azure DevOps para configurar pipelines

## 🚀 Deployment Manual (Terraform)

### 1. Configuração Inicial

1. **Clone o repositório e navegue para o diretório do Terraform:**
   ```bash
   cd azure-dashboard/terraform
   ```

2. **Configure suas credenciais Azure:**
   ```bash
   az login
   az account set --subscription "sua-subscription-id"
   ```

3. **Copie e configure o arquivo de variáveis:**
   ```bash
   cp terraform.tfvars.example terraform.tfvars
   ```

4. **Edite o arquivo `terraform.tfvars` com suas configurações:**
   ```hcl
   # Configurações básicas
   environment = "dev"
   location    = "East US"
   
   # Credenciais do Azure
   azure_tenant_id       = "seu-tenant-id"
   azure_client_id       = "seu-client-id"
   azure_client_secret   = "seu-client-secret"
   azure_subscription_id = "sua-subscription-id"
   
   # Outras configurações...
   ```

### 2. Deployment Automatizado

Execute o script de setup que automatiza todo o processo:

```bash
./setup.sh dev    # Para ambiente de desenvolvimento
./setup.sh prod   # Para ambiente de produção
```

### 3. Deployment Manual (Passo a Passo)

Se preferir executar manualmente:

1. **Criar backend do Terraform:**
   ```bash
   # Criar resource group para o state
   az group create --name terraform-state-rg --location "East US"
   
   # Criar storage account (substitua XXXX por números aleatórios)
   az storage account create \
     --resource-group terraform-state-rg \
     --name terraformstateboltXXXX \
     --sku Standard_LRS \
     --encryption-services blob
   
   # Criar container
   az storage container create \
     --name tfstate \
     --account-name terraformstateboltXXXX
   ```

2. **Configurar backend do Terraform:**
   ```bash
   # Criar arquivo backend.tf
   cat > backend.tf << EOF
   terraform {
     backend "azurerm" {
       resource_group_name  = "terraform-state-rg"
       storage_account_name = "terraformstateboltXXXX"
       container_name       = "tfstate"
       key                  = "bolt.tfstate"
     }
   }
   EOF
   ```

3. **Executar Terraform:**
   ```bash
   terraform init
   terraform validate
   terraform plan -var-file="environments/dev.tfvars"
   terraform apply -var-file="environments/dev.tfvars"
   ```

## 🔄 Deployment com Azure DevOps (CI/CD)

### 1. Configuração do Azure DevOps

1. **Criar Service Connection:**
   - Vá para Project Settings > Service connections
   - Crie uma nova Azure Resource Manager connection
   - Use Service Principal (automatic) ou configure manualmente

2. **Configurar Variable Groups:**
   ```yaml
   # Criar variable group "BOLT-Variables"
   azureServiceConnection: 'Azure-ServiceConnection'
   terraformVersion: '1.5.0'
   nodeVersion: '18.x'
   pythonVersion: '3.9'
   ```

3. **Configurar Environments:**
   - Crie environments: `dev`, `staging`, `prod`
   - Configure approvals para produção

### 2. Configuração da Pipeline

1. **Importe a pipeline:**
   - Use o arquivo `pipelines/azure-pipelines.yml`
   - Configure as variáveis necessárias

2. **Configure os triggers:**
   - Branch policies para `main` e `develop`
   - Path filters para evitar builds desnecessários

### 3. Execução da Pipeline

A pipeline executa automaticamente quando:
- Há push para `main` ou `develop`
- É criado um Pull Request

Estágios da pipeline:
1. **Validate** - Validação e testes
2. **Infrastructure** - Provisiona infraestrutura
3. **Applications** - Deploy das aplicações
4. **PostDeploy** - Verificações de saúde

## 📁 Estrutura do Projeto

```
azure-dashboard/
├── terraform/                 # Configurações Terraform
│   ├── modules/               # Módulos reutilizáveis
│   │   ├── app-service/       # App Services
│   │   ├── function-app/      # Azure Functions
│   │   ├── networking/        # Rede e segurança
│   │   └── storage/           # Storage Account
│   ├── environments/          # Configurações por ambiente
│   │   ├── dev.tfvars
│   │   └── prod.tfvars
│   ├── main.tf               # Configuração principal
│   ├── variables.tf          # Definição de variáveis
│   ├── outputs.tf            # Outputs
│   └── setup.sh              # Script de deployment
├── pipelines/                # Pipelines Azure DevOps
│   └── azure-pipelines.yml
├── azure-dashboard-frontend/ # Aplicação React
├── azure-dashboard-backend/  # API Flask
└── azure-functions-project/  # Azure Functions
```

## 🔧 Configurações por Ambiente

### Desenvolvimento (dev)
- App Service Plan: F1 (Free)
- Application Insights: Habilitado
- Backup: Desabilitado
- CORS: Permissivo (*)

### Produção (prod)
- App Service Plan: B1 (Basic)
- Application Insights: Habilitado
- Backup: Habilitado (30 dias)
- CORS: Restritivo (domínios específicos)

## 📊 Monitoramento

### Application Insights
- Métricas de performance
- Logs de aplicação
- Alertas personalizados

### Health Checks
- Frontend: `https://app-url/`
- Backend: `https://api-url/health`
- Functions: `https://func-url/api/status`

## 🔒 Segurança

### Configurações Implementadas
- HTTPS obrigatório
- TLS 1.2 mínimo
- Network Security Groups
- Identidade gerenciada para Functions
- Secrets via Azure Key Vault (recomendado)

### Variáveis Sensíveis
Nunca commite no código:
- `azure_client_secret`
- `jwt_secret_key`
- `database_connection_string`

Use Azure DevOps Variable Groups ou Azure Key Vault.

## 🚨 Troubleshooting

### Problemas Comuns

1. **Erro de permissões:**
   ```bash
   # Verificar permissões
   az role assignment list --assignee $(az account show --query user.name -o tsv)
   ```

2. **Terraform state lock:**
   ```bash
   # Forçar unlock (use com cuidado)
   terraform force-unlock LOCK_ID
   ```

3. **App Service não inicia:**
   - Verificar logs no portal Azure
   - Verificar configurações de runtime
   - Verificar variáveis de ambiente

### Logs e Diagnóstico

1. **Terraform:**
   ```bash
   export TF_LOG=DEBUG
   terraform apply
   ```

2. **Azure CLI:**
   ```bash
   az configure --defaults group=bolt-dev-rg
   az webapp log tail --name bolt-dev-frontend
   ```

## 📞 Suporte

Para problemas ou dúvidas:
1. Verificar logs no Application Insights
2. Consultar documentação do Azure
3. Contatar a equipe de DevOps

## 🔄 Atualizações

### Atualizar Infraestrutura
```bash
cd terraform
terraform plan -var-file="environments/prod.tfvars"
terraform apply -var-file="environments/prod.tfvars"
```

### Atualizar Aplicações
Use a pipeline do Azure DevOps ou:
```bash
# Frontend
cd azure-dashboard-frontend
npm run build
az webapp deployment source config-zip --src dist.zip

# Backend
cd azure-dashboard-backend
az webapp deployment source config-zip --src backend.zip
```

## 📝 Changelog

### v1.0.0
- Configuração inicial do Terraform
- Pipeline básica do Azure DevOps
- Deployment automatizado
- Monitoramento com Application Insights

