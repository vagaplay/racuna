# 🚀 BOLT Dashboard - Início Rápido Local

## ⚡ Setup em 3 Passos

### 1. Baixar o Projeto
```bash
# Copie a pasta azure-dashboard para sua máquina
# Ou baixe os arquivos do sandbox
```

### 2. Executar Setup
```bash
cd azure-dashboard
./setup-local.sh
```

### 3. Configurar Azure
```bash
# Edite o arquivo:
nano azure-dashboard-backend/.env

# Adicione suas credenciais:
AZURE_TENANT_ID=seu_tenant_id
AZURE_CLIENT_ID=seu_client_id  
AZURE_CLIENT_SECRET=seu_client_secret
AZURE_SUBSCRIPTION_ID=seu_subscription_id
```

### 4. Executar
```bash
./start-local.sh
```

## 🌐 Acessar

- **Frontend**: http://localhost:5173
- **Backend**: http://localhost:5000

## 🔑 Como Obter Credenciais Azure

### Service Principal (Recomendado)
```bash
az ad sp create-for-rbac --name "bolt-dashboard-local" \
    --role "Reader" \
    --scopes "/subscriptions/YOUR_SUBSCRIPTION_ID"
```

### Resultado:
```json
{
  "appId": "CLIENT_ID",
  "displayName": "bolt-dashboard-local", 
  "password": "CLIENT_SECRET",
  "tenant": "TENANT_ID"
}
```

### Subscription ID:
```bash
az account show --query id --output tsv
```

## 🎯 Funcionalidades Locais

### ✅ O que funciona:
- **Dashboard**: Interface completa
- **Login**: Sistema de autenticação
- **Azure APIs**: Conexão direta com Azure
- **Recursos**: Lista seus recursos reais
- **Custos**: Dados reais de billing
- **Monitoramento**: Métricas dos recursos
- **Ações**: Criar locks, políticas
- **Configurações**: Gerenciar credenciais

### 🔒 Segurança:
- **Dados locais**: Tudo fica na sua máquina
- **Criptografia**: Credenciais criptografadas
- **HTTPS**: Comunicação segura com Azure
- **Isolado**: Sem exposição externa

## 🛠️ Comandos Úteis

### Desenvolvimento:
```bash
# Só backend
./start-backend.sh

# Só frontend  
./start-frontend.sh

# Ambos
./start-local.sh

# Parar tudo
Ctrl+C
```

### Debug:
```bash
# Logs backend
tail -f azure-dashboard-backend/backend.log

# Testar API
curl http://localhost:5000/api/health

# Verificar banco
sqlite3 azure-dashboard-backend/bolt_dashboard.db
```

## 🚨 Problemas Comuns

### "Porta em uso":
```bash
# Verificar processos
lsof -i :5000  # Backend
lsof -i :5173  # Frontend

# Matar processo
kill -9 <PID>
```

### "Módulo não encontrado":
```bash
cd azure-dashboard-backend
source venv/bin/activate
pip install -r requirements.txt
```

### "CORS Error":
- Verificar se backend está rodando
- Verificar URL no frontend (.env.local)

## 🎉 Pronto!

Agora você tem o BOLT Dashboard rodando localmente e se comunicando diretamente com o Azure!

**Acesse: http://localhost:5173** 🚀

