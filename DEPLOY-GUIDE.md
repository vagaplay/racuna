# 🚀 GUIA DE DEPLOY RÁPIDO - BOLT DASHBOARD

## ⚡ DEPLOY EM 5 MINUTOS

### Pré-requisitos ✅
- [x] Conta Azure ativa
- [x] Service Principal configurado (já feito)
- [x] Azure CLI instalado

### Passo 1: Download do Projeto
```bash
# Baixar e extrair o projeto
# (você já tem os arquivos)
cd bolt-dashboard-containerized
```

### Passo 2: Verificar Configurações
```bash
# Verificar se credenciais estão corretas
cat .env | grep AZURE_
```

### Passo 3: Deploy Completo
```bash
# 1. Criar infraestrutura Azure (5-10 minutos)
./scripts/azure-setup.sh

# 2. Build e deploy da aplicação (3-5 minutos)
./scripts/build-and-deploy.sh

# 3. Configurar automações (2-3 minutos)
./scripts/setup-automation.sh
./scripts/setup-budget-automation.sh
```

### Passo 4: Teste
```bash
# Testar sistema completo
./scripts/test-system.sh
```

### Passo 5: Acesso
```bash
# A URL será exibida no final do deploy
# Login: test@test.com
# Senha: 123456
```

## 🎯 RESULTADO ESPERADO

Após o deploy você terá:

### ✅ Aplicação Web Funcionando
- Dashboard moderno e responsivo
- Todas as funcionalidades do projeto original
- Comunicação frontend ↔ backend resolvida

### ✅ Automações Configuradas
- Budget automation (lógica budgetbasa)
- Shutdown automático de recursos
- Limpeza por tags
- Remoção automática de locks

### ✅ Infraestrutura Econômica
- Container Instance (~R$ 36/mês)
- Container Registry (~R$ 25/mês)
- Key Vault (~R$ 5/mês)
- Storage Account (~R$ 10/mês)
- **Total: ~R$ 81/mês**

## 🔧 COMANDOS ÚTEIS

### Monitoramento
```bash
# Status da aplicação
az container show --name bolt-dashboard-ci --resource-group rg-bolt-dashboard

# Logs da aplicação
az container logs --name bolt-dashboard-ci --resource-group rg-bolt-dashboard

# Status dos runbooks
az automation job list --automation-account-name aa-bolt-dashboard --resource-group rg-bolt-dashboard
```

### Manutenção
```bash
# Restart da aplicação
az container restart --name bolt-dashboard-ci --resource-group rg-bolt-dashboard

# Atualizar aplicação
./scripts/build-and-deploy.sh

# Teste completo
./scripts/test-system.sh
```

## 🚨 TROUBLESHOOTING RÁPIDO

### Problema: Script falha no azure-setup.sh
**Solução:**
```bash
# Verificar login
az account show

# Verificar permissões
az role assignment list --assignee 7d49dfab-0f44-4972-9ef1-894de8918b41
```

### Problema: Build falha
**Solução:**
```bash
# Verificar Docker
docker --version

# Login manual no ACR
az acr login --name boltdashboardacr2024
```

### Problema: Aplicação não responde
**Solução:**
```bash
# Verificar status
az container show --name bolt-dashboard-ci --resource-group rg-bolt-dashboard --query instanceView.state

# Aguardar inicialização (pode levar 2-3 minutos)
```

### Problema: Webhook não funciona
**Solução:**
```bash
# Verificar URL
cat azure-resources.txt | grep WEBHOOK_URL

# Testar manualmente
curl -X POST 'WEBHOOK_URL' -H 'Content-Type: application/json' -d '{"test":"true"}'
```

## 📊 MONITORAMENTO DE CUSTOS

### Verificar Gastos Atuais
```bash
# Via Azure CLI
az consumption usage list --top 10

# Via Portal Azure
# Subscriptions > Cost Management > Cost analysis
```

### Configurar Alertas Adicionais
```bash
# O sistema já cria alertas em 50%, 75%, 90% e 100%
# Para alertas customizados, use o portal Azure
```

## 🔒 SEGURANÇA

### Credenciais Já Configuradas
- ✅ Service Principal: 7d49dfab-0f44-4972-9ef1-894de8918b41
- ✅ Tenant: 8245f66a-b3fa-4019-9bdd-746320d1855c
- ✅ Subscription: d5da2aa9-040f-4924-ad21-97105d90a8bb

### Recursos Protegidos
Por padrão, estes Resource Groups são protegidos:
- rg-bolt-dashboard
- rg-production
- rg-critical
- NetworkWatcherRG

### Adicionar Proteção HoldLock
```bash
# Para proteger um Resource Group específico
az lock create --name HoldLock --lock-type CanNotDelete --resource-group NOME_DO_RG
```

## 🎉 PRÓXIMOS PASSOS

### Após Deploy Bem-sucedido
1. **Acesse a aplicação** e explore todas as funcionalidades
2. **Configure budgets** personalizados via dashboard
3. **Teste automações** em modo "show" primeiro
4. **Configure emails** de notificação
5. **Documente recursos críticos** que precisam de HoldLock

### Para Produção
1. **Altere a senha padrão** do usuário test@test.com
2. **Configure HTTPS customizado** se necessário
3. **Configure backup** automático dos dados
4. **Configure monitoramento** avançado
5. **Documente procedimentos** para sua equipe

## 📞 SUPORTE

### Em Caso de Problemas
1. Execute: `./scripts/test-system.sh`
2. Verifique logs: `az container logs --name bolt-dashboard-ci --resource-group rg-bolt-dashboard`
3. Consulte este guia de troubleshooting
4. Se necessário, execute novamente os scripts de setup

### Recursos Úteis
- **Portal Azure**: portal.azure.com
- **Documentação Azure**: docs.microsoft.com/azure
- **Azure CLI Reference**: docs.microsoft.com/cli/azure

---

**🎯 OBJETIVO**: Ter o BOLT Dashboard funcionando em produção em menos de 15 minutos!

**💰 CUSTO**: ~R$ 81/mês (85% mais barato que App Service Premium)

**🔧 MANUTENÇÃO**: Mínima - sistema totalmente automatizado

