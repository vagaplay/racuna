# BOLT DASHBOARD - CONTAINERIZADO

Sistema completo de gerenciamento Azure com automação de budget e recursos, baseado no projeto original BOLT Dashboard + lógica do projeto budgetbasa.

## 🎯 VISÃO GERAL

O BOLT Dashboard é uma solução completa para gerenciamento de recursos Azure que combina:

- ✅ **Dashboard Web Moderno** (React + Flask)
- ✅ **Automação de Budget** (lógica do projeto budgetbasa)
- ✅ **Containerização Completa** (Docker + Azure Container Instances)
- ✅ **Automação de Recursos** (shutdown, cleanup, locks)
- ✅ **Deploy Automatizado** (scripts prontos)

## 🚀 INÍCIO RÁPIDO

### Pré-requisitos
- Conta Azure com Service Principal configurado
- Docker instalado (para desenvolvimento local)
- Azure CLI instalado

### Deploy em 3 Passos

```bash
# 1. Configurar infraestrutura Azure
./scripts/azure-setup.sh

# 2. Build e deploy da aplicação
./scripts/build-and-deploy.sh

# 3. Configurar automações
./scripts/setup-automation.sh
./scripts/setup-budget-automation.sh
```

### Acesso
- **URL**: Será fornecida após o deploy
- **Login**: test@test.com
- **Senha**: 123456

## 📋 FUNCIONALIDADES

### Dashboard Web
- 🏠 **Dashboard Principal**: Visão geral dos recursos Azure
- 💰 **Orçamento e Custos**: Monitoramento de gastos com alertas
- 📊 **Monitoramento**: Status de recursos e alertas
- ⏰ **Agendamentos**: Tarefas programadas e automações
- 📈 **Relatórios**: Análises e exportação de dados
- ⚙️ **Configurações**: Credenciais Azure e configurações

### Automações (Projeto Budgetbasa)
- 💸 **Budget Automation**: Ações automáticas quando budget é excedido
- 🔒 **Resource Protection**: Sistema de locks (HoldLock)
- ⏰ **Scheduled Shutdown**: Desligamento automático de recursos
- 🏷️ **Tag-based Cleanup**: Limpeza baseada em tags de expiração
- 🔓 **Lock Management**: Remoção automática de locks da subscription

### Containerização
- 🐳 **Docker Multi-stage**: Build otimizado
- 🔄 **Nginx Reverse Proxy**: Resolve comunicação frontend ↔ backend
- 📦 **Azure Container Instances**: Deploy econômico
- 💾 **Persistent Storage**: Dados preservados entre deploys

## 🏗️ ARQUITETURA

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend       │    │   Azure APIs   │
│   (React)       │◄──►│   (Flask)       │◄──►│   (Cost, etc)   │
│   Port 3000     │    │   Port 5000     │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │   Nginx         │
                    │   Port 80       │
                    │   (Reverse      │
                    │    Proxy)       │
                    └─────────────────┘
                                 │
                    ┌─────────────────┐
                    │   Container     │
                    │   Instance      │
                    │   (Azure)       │
                    └─────────────────┘
```

## 💰 CUSTOS

### Infraestrutura Econômica (3 usuários)
- **Container Instance**: ~R$ 36/mês
- **Container Registry**: ~R$ 25/mês
- **Key Vault**: ~R$ 5/mês
- **Storage Account**: ~R$ 10/mês
- **Automation Account**: ~R$ 5/mês
- **TOTAL**: ~R$ 81/mês

### Comparação com App Service Premium
- **App Service Premium**: ~R$ 400/mês
- **Economia**: 85% (R$ 319/mês)

## 📁 ESTRUTURA DO PROJETO

```
bolt-dashboard-containerized/
├── 📁 azure-dashboard-frontend/     # Frontend React (projeto original)
├── 📁 azure-dashboard-backend/      # Backend Flask (projeto original)
├── 📁 scripts/                     # Scripts de automação
│   ├── azure-setup.sh              # Setup infraestrutura Azure
│   ├── build-and-deploy.sh         # Build e deploy
│   ├── setup-automation.sh         # Configurar automações
│   ├── setup-budget-automation.sh  # Configurar budget automation
│   └── test-system.sh              # Testes do sistema
├── 🐳 Dockerfile                   # Containerização
├── 🔧 docker-compose.yml           # Desenvolvimento local
├── 🔐 .env                         # Configurações (com credenciais)
├── 📝 .env.template                # Template de configurações
└── 📋 README.md                    # Esta documentação
```

## ⚙️ CONFIGURAÇÃO

### Credenciais Azure (Já Configuradas)
```bash
AZURE_TENANT_ID=8245f66a-b3fa-4019-9bdd-746320d1855c
AZURE_CLIENT_ID=7d49dfab-0f44-4972-9ef1-894de8918b41
AZURE_CLIENT_SECRET=~cP8Q~rx6pY9r4EOqmmMfeKdZKoTPtBatK02NaZF
AZURE_SUBSCRIPTION_ID=d5da2aa9-040f-4924-ad21-97105d90a8bb
```

### Configurações de Automação
```bash
SHUTDOWN_TIME=19:00                 # Horário para desligar recursos
TIMEZONE=America/Sao_Paulo          # Fuso horário
LOCK_REMOVAL_DAY=2                  # Dia do mês para remover locks
DEFAULT_BUDGET_AMOUNT=100           # Budget padrão em USD
```

## 🤖 AUTOMAÇÕES CONFIGURADAS

### 1. Budget Automation (Lógica Budgetbasa)
- **Trigger**: Budget atinge 100%
- **Ação**: Webhook → Runbook
- **Processo**:
  1. Verifica RGs com HoldLock (protegidos)
  2. Remove outros locks
  3. Exclui RGs não protegidos (ou mostra, conforme configuração)
  4. Adiciona lock ReadOnly na subscription

### 2. Scheduled Shutdown
- **Horário**: 19:00 (configurável)
- **Recursos**: VMs, Web Apps
- **Ação**: Desligamento automático

### 3. Tag-based Cleanup
- **Horário**: 20:00 diariamente
- **Critério**: Tags ExpireOn vencidas ou ausentes
- **Ação**: Exclusão ou relatório

### 4. Lock Removal
- **Frequência**: Dia 2 de cada mês (configurável)
- **Ação**: Remove locks de budget da subscription

## 🧪 TESTES

### Teste Completo do Sistema
```bash
./scripts/test-system.sh
```

### Testes Manuais

#### 1. Aplicação Web
```bash
# Acesse a URL fornecida após deploy
# Login: test@test.com / 123456
```

#### 2. Webhook de Budget
```bash
curl -X POST 'WEBHOOK_URL' \
  -H 'Content-Type: application/json' \
  -d '{"subscriptionId":"SUBSCRIPTION_ID","action":"show"}'
```

#### 3. Runbook Manual
```bash
az automation runbook start \
  --automation-account-name aa-bolt-dashboard \
  --resource-group rg-bolt-dashboard \
  --name ShutdownResourcesRunbook \
  --parameters action=show
```

## 🔧 DESENVOLVIMENTO LOCAL

### Usando Docker Compose
```bash
# Iniciar aplicação
docker-compose up -d

# Acessar
http://localhost:8080

# Ver logs
docker-compose logs -f

# Parar
docker-compose down
```

### Build Manual
```bash
# Build da imagem
docker build -t bolt-dashboard .

# Executar localmente
docker run -p 8080:80 \
  --env-file .env \
  -v bolt_data:/app/data \
  bolt-dashboard
```

## 🛠️ MANUTENÇÃO

### Atualizar Aplicação
```bash
# Rebuild e redeploy
./scripts/build-and-deploy.sh
```

### Backup de Dados
```bash
# Dados são automaticamente persistidos no Azure File Share
# Para backup manual:
az storage file download-batch \
  --destination ./backup \
  --source bolt-dashboard-data \
  --account-name STORAGE_ACCOUNT_NAME
```

### Monitoramento
```bash
# Logs do Container Instance
az container logs \
  --name bolt-dashboard-ci \
  --resource-group rg-bolt-dashboard

# Status dos runbooks
az automation job list \
  --automation-account-name aa-bolt-dashboard \
  --resource-group rg-bolt-dashboard
```

## 🔒 SEGURANÇA

### Credenciais
- ✅ Service Principal com permissões mínimas
- ✅ Secrets armazenados no Key Vault
- ✅ Client Secret criptografado nas variáveis de automação

### Proteção de Recursos
- ✅ Sistema de HoldLock para recursos críticos
- ✅ Lista de Resource Groups protegidos
- ✅ Aprovação manual para ações críticas

### Rede
- ✅ HTTPS automático via Azure
- ✅ CORS configurado adequadamente
- ✅ Health checks implementados

## 📞 SUPORTE

### Logs e Troubleshooting
```bash
# Logs da aplicação
az container logs --name bolt-dashboard-ci --resource-group rg-bolt-dashboard

# Status dos recursos
./scripts/test-system.sh

# Verificar budget
az consumption budget list --subscription SUBSCRIPTION_ID
```

### Problemas Comuns

#### 1. Aplicação não responde
```bash
# Verificar status
az container show --name bolt-dashboard-ci --resource-group rg-bolt-dashboard

# Restart
az container restart --name bolt-dashboard-ci --resource-group rg-bolt-dashboard
```

#### 2. Webhook não funciona
```bash
# Verificar URL do webhook
cat azure-resources.txt | grep WEBHOOK_URL

# Testar manualmente
curl -X POST 'WEBHOOK_URL' -d '{"test":"true"}'
```

#### 3. Runbooks falham
```bash
# Verificar variáveis
az automation variable list --automation-account-name aa-bolt-dashboard --resource-group rg-bolt-dashboard

# Verificar permissões do Service Principal
az role assignment list --assignee CLIENT_ID
```

## 🎉 PRÓXIMOS PASSOS

### Após Deploy
1. ✅ Acesse a aplicação e teste todas as funcionalidades
2. ✅ Configure budgets personalizados
3. ✅ Teste automações em modo "show"
4. ✅ Configure emails de notificação
5. ✅ Documente recursos críticos com HoldLock

### Melhorias Futuras
- 🔄 Migração para Azure DevOps CI/CD
- 📱 Interface mobile responsiva
- 🔔 Notificações push
- 📊 Dashboards avançados
- 🤖 IA para otimização de custos

## 📄 LICENÇA

Este projeto é baseado no BOLT Dashboard original e incorpora a lógica do projeto budgetbasa.

---

**BOLT Dashboard Containerizado** - Solução completa para gerenciamento Azure com automação inteligente de custos e recursos.

*Desenvolvido com base no projeto original e melhorado com containerização e automações avançadas.*

