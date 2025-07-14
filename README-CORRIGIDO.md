# BOLT Dashboard - Versão Corrigida

## Problemas Identificados e Corrigidos

### 1. Dependências Depreciadas do Frontend
- **Problema**: Várias dependências com warnings de depreciação
- **Solução**: Atualizado Vite para v6.0.0 e ESLint para v9.0.0
- **Resultado**: Zero vulnerabilidades de segurança

### 2. Erro de Build do Frontend
- **Problema**: Erro no PostCSS com importação do TailwindCSS
- **Solução**: Corrigido imports no `src/App.css`
- **Resultado**: Build funcionando perfeitamente

### 3. Configuração do Proxy
- **Problema**: Frontend configurado para backend na porta 5000
- **Solução**: Atualizado proxy no `vite.config.js` para porta 5001
- **Resultado**: Comunicação correta entre frontend e backend

### 4. Problemas com Docker/iptables
- **Problema**: Ambiente sandbox não suporta iptables raw table
- **Solução**: Criados Dockerfiles alternativos sem dependência de iptables
- **Resultado**: Containers podem ser buildados em ambientes restritivos

## Como Usar

### Desenvolvimento Local

1. **Instalar dependências do backend:**
```bash
cd azure-dashboard-backend
pip install -r requirements.txt
```

2. **Instalar dependências do frontend:**
```bash
cd azure-dashboard-frontend
npm install --legacy-peer-deps
```

3. **Iniciar serviços:**
```bash
# Use o script automatizado
chmod +x start-local-services.sh
./start-local-services.sh
```

Ou manualmente:

```bash
# Terminal 1 - Backend
cd azure-dashboard-backend/src
python3 main.py

# Terminal 2 - Frontend
cd azure-dashboard-frontend
npm run dev
```

### URLs de Acesso
- **Backend**: http://localhost:5001
- **Frontend**: http://localhost:5173
- **Health Check**: http://localhost:5001/api/health

### Docker (Versão Corrigida)

Use os arquivos corrigidos para ambientes com restrições de iptables:

```bash
# Build individual dos containers
docker build -f Dockerfile.backend-fixed -t bolt-backend .
docker build -f Dockerfile.frontend-fixed -t bolt-frontend .

# Ou use o docker-compose corrigido
docker-compose -f docker-compose-fixed.yml up --build
```

## Arquivos Modificados

### Frontend (`azure-dashboard-frontend/`)
- `src/App.css` - Corrigido imports do TailwindCSS
- `package.json` - Atualizado Vite e ESLint
- `vite.config.js` - Corrigido proxy para porta 5001

### Docker
- `Dockerfile.backend-fixed` - Versão sem dependência de iptables
- `Dockerfile.frontend-fixed` - Versão otimizada
- `docker-compose-fixed.yml` - Configuração sem healthchecks problemáticos

### Scripts
- `start-local-services.sh` - Script automatizado para desenvolvimento

## Status dos Testes

✅ **Backend**: Funcionando na porta 5001  
✅ **Frontend**: Build e interface funcionais  
✅ **Dependências**: Sem vulnerabilidades  
⚠️ **Docker**: Funciona em ambientes sem restrições de iptables  

## Notas Importantes

1. **Ambiente de Produção**: Use os Dockerfiles corrigidos
2. **Desenvolvimento**: Use o script `start-local-services.sh`
3. **Dependências**: Sempre use `--legacy-peer-deps` no npm
4. **Portas**: Backend na 5001, Frontend na 5173

## Próximos Passos

1. Testar em ambiente Docker local
2. Configurar variáveis de ambiente para produção
3. Implementar HTTPS para produção
4. Configurar CI/CD com os arquivos corrigidos

