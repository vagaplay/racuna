# 🔑 BOLT Dashboard - Configuração de Credenciais Azure

## ⚡ **SETUP SUPER RÁPIDO (3 minutos)**

### 1. **Baixar e Extrair o Projeto**
```bash
# Extrair o arquivo
tar -xzf bolt-dashboard-completo.tar.gz
cd azure-dashboard
```

### 2. **Executar Setup Automático**
```bash
./setup-local.sh
```

### 3. **Configurar Credenciais Azure**
```bash
# Editar arquivo de configuração
nano .env

# OU usar qualquer editor de texto
code .env
gedit .env
```

### 4. **Preencher Credenciais no arquivo .env**
```env
# Suas credenciais Azure
AZURE_TENANT_ID=seu_tenant_id_aqui
AZURE_CLIENT_ID=seu_client_id_aqui
AZURE_CLIENT_SECRET=seu_client_secret_aqui
AZURE_SUBSCRIPTION_ID=seu_subscription_id_aqui
```

### 5. **Executar Dashboard**
```bash
./start-local.sh
```

### 6. **Acessar**
- **Frontend**: http://localhost:5173
- **Backend**: http://localhost:5000

---

## 🔑 **COMO OBTER CREDENCIAIS AZURE**

### **Opção 1: Azure CLI (Recomendado)**
```bash
# 1. Fazer login no Azure
az login

# 2. Criar Service Principal
az ad sp create-for-rbac --name "bolt-dashboard-local" \
    --role "Reader" \
    --scopes "/subscriptions/$(az account show --query id -o tsv)"

# 3. Obter IDs necessários
az account show --query "{tenantId:tenantId, subscriptionId:id}" -o table
```

### **Resultado do comando acima:**
```json
{
  "appId": "12345678-1234-1234-1234-123456789012",        # ← AZURE_CLIENT_ID
  "displayName": "bolt-dashboard-local",
  "password": "abcdef12-3456-7890-abcd-ef1234567890",     # ← AZURE_CLIENT_SECRET
  "tenant": "87654321-4321-4321-4321-210987654321"       # ← AZURE_TENANT_ID
}
```

### **Opção 2: Portal Azure**
1. **Azure Active Directory** → **App registrations** → **New registration**
2. **Nome**: "BOLT Dashboard Local"
3. **Supported account types**: Single tenant
4. **Redirect URI**: Deixar vazio
5. **Register**
6. **Copiar Application (client) ID** → `AZURE_CLIENT_ID`
7. **Directory (tenant) ID** → `AZURE_TENANT_ID`
8. **Certificates & secrets** → **New client secret** → Copiar valor → `AZURE_CLIENT_SECRET`
9. **Subscriptions** → Copiar **Subscription ID** → `AZURE_SUBSCRIPTION_ID`

---

## 📋 **EXEMPLO DE ARQUIVO .env PREENCHIDO**

```env
# ========================================
# 🔑 CREDENCIAIS AZURE (OBRIGATÓRIO)
# ========================================

# Tenant ID do Azure AD
AZURE_TENANT_ID=87654321-4321-4321-4321-210987654321

# Client ID do Service Principal
AZURE_CLIENT_ID=12345678-1234-1234-1234-123456789012

# Client Secret do Service Principal
AZURE_CLIENT_SECRET=abcdef12-3456-7890-abcd-ef1234567890

# Subscription ID da sua conta Azure
AZURE_SUBSCRIPTION_ID=11111111-2222-3333-4444-555555555555

# Nome da Subscription (opcional)
AZURE_SUBSCRIPTION_NAME=Minha Subscription Azure

# ========================================
# 🔧 OUTRAS CONFIGURAÇÕES (Já preenchidas)
# ========================================
# (O resto das configurações já vem pronto)
```

---

## 🚨 **TROUBLESHOOTING**

### **Problema: "Authentication failed"**
```bash
# Verificar se credenciais estão corretas
az login --service-principal \
    -u $AZURE_CLIENT_ID \
    -p $AZURE_CLIENT_SECRET \
    --tenant $AZURE_TENANT_ID
```

### **Problema: "Subscription not found"**
```bash
# Listar subscriptions disponíveis
az account list --output table
```

### **Problema: "Permission denied"**
```bash
# Verificar permissões do Service Principal
az role assignment list --assignee $AZURE_CLIENT_ID --output table
```

### **Problema: "Module not found"**
```bash
# Reinstalar dependências
cd azure-dashboard-backend
source venv/bin/activate
pip install -r requirements.txt
```

---

## ✅ **CHECKLIST DE VERIFICAÇÃO**

- [ ] ✅ Extraí o projeto: `tar -xzf bolt-dashboard-completo.tar.gz`
- [ ] ✅ Executei setup: `./setup-local.sh`
- [ ] ✅ Editei arquivo: `.env`
- [ ] ✅ Preenchi: `AZURE_TENANT_ID`
- [ ] ✅ Preenchi: `AZURE_CLIENT_ID`
- [ ] ✅ Preenchi: `AZURE_CLIENT_SECRET`
- [ ] ✅ Preenchi: `AZURE_SUBSCRIPTION_ID`
- [ ] ✅ Executei: `./start-local.sh`
- [ ] ✅ Acessei: http://localhost:5173

---

## 🎯 **RESULTADO ESPERADO**

Após seguir todos os passos:

1. **Backend rodando** em http://localhost:5000
2. **Frontend rodando** em http://localhost:5173
3. **Login funcionando** com suas credenciais
4. **Dashboard mostrando** seus recursos Azure reais
5. **Custos exibindo** dados da sua subscription
6. **Todas as funcionalidades** operacionais

---

## 📞 **SUPORTE**

Se tiver problemas:

1. **Verificar logs** nos terminais
2. **Conferir credenciais** no arquivo .env
3. **Testar conexão** Azure separadamente
4. **Verificar permissões** do Service Principal

**Com essas instruções, você terá o BOLT Dashboard funcionando em 3 minutos!** 🚀

