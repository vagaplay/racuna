# BOLT Dashboard - Instruções Docker

## 🐳 **SETUP COMPLETO COM DOCKER**

### **📋 Pré-requisitos**
- Docker instalado
- Docker Compose instalado
- Pelo menos 4GB RAM disponível
- Portas 80 e 5001 livres

### **📁 Estrutura de Arquivos**
Coloque os arquivos Docker na raiz do projeto:
```
bolt-dashboard/
├── azure-dashboard-backend/
├── azure-dashboard-frontend/
├── Dockerfile.backend          ⭐ NOVO
├── Dockerfile.frontend         ⭐ NOVO
├── docker-compose.yml          ⭐ NOVO
├── nginx.conf                  ⭐ NOVO
├── .dockerignore              ⭐ NOVO
├── .env.docker                ⭐ NOVO
├── docker-start.sh            ⭐ NOVO
└── docker-stop.sh             ⭐ NOVO
```

---

## 🚀 **INICIALIZAÇÃO RÁPIDA**

### **Método 1: Script Automático (Recomendado)**
```bash
# Dar permissão de execução
chmod +x docker-start.sh docker-stop.sh

# Iniciar tudo automaticamente
./docker-start.sh
```

### **Método 2: Manual**
```bash
# 1. Criar diretórios
mkdir -p data logs

# 2. Copiar variáveis de ambiente
cp .env.docker .env

# 3. Build e start
docker-compose up -d --build

# 4. Verificar status
docker-compose ps
```

---

## 📱 **ACESSAR APLICAÇÃO**

Após inicialização bem-sucedida:
- **Frontend:** http://localhost
- **Backend API:** http://localhost:5001
- **Login padrão:** test@test.com / 123456

---

## 🛠️ **COMANDOS ÚTEIS**

### **Gerenciamento Básico**
```bash
# Ver logs em tempo real
docker-compose logs -f

# Ver logs específicos
docker-compose logs backend
docker-compose logs frontend

# Reiniciar serviços
docker-compose restart

# Parar tudo
docker-compose down

# Parar e remover volumes (APAGA DADOS)
docker-compose down -v
```

### **Debugging**
```bash
# Entrar no container do backend
docker-compose exec backend bash

# Entrar no container do frontend
docker-compose exec frontend sh

# Ver uso de recursos
docker stats

# Verificar redes
docker network ls
```

### **Manutenção**
```bash
# Rebuild sem cache
docker-compose build --no-cache

# Limpar sistema Docker
docker system prune -f

# Ver imagens
docker images

# Remover imagens não utilizadas
docker image prune -f
```

---

## 🔧 **CONFIGURAÇÕES AVANÇADAS**

### **Variáveis de Ambiente (.env)**
```bash
# Editar configurações
nano .env

# Principais variáveis:
FLASK_ENV=production
DATABASE_URL=sqlite:///data/bolt_dashboard.db
CORS_ORIGINS=http://localhost
LOG_LEVEL=INFO
```

### **Portas Customizadas**
Para mudar portas, edite `docker-compose.yml`:
```yaml
services:
  frontend:
    ports:
      - "8080:80"  # Frontend na porta 8080
  backend:
    ports:
      - "5002:5001"  # Backend na porta 5002
```

### **Banco PostgreSQL (Opcional)**
Descomente no `docker-compose.yml`:
```yaml
database:
  image: postgres:15-alpine
  # ... resto da configuração
```

E altere no `.env`:
```bash
DATABASE_URL=postgresql://bolt_user:bolt_password@database:5432/bolt_dashboard
```

---

## 🚨 **TROUBLESHOOTING**

### **Erro: "Port already in use"**
```bash
# Verificar o que está usando a porta
sudo lsof -i :80
sudo lsof -i :5001

# Parar processo ou mudar porta no docker-compose.yml
```

### **Erro: "No space left on device"**
```bash
# Limpar Docker
docker system prune -a -f
docker volume prune -f
```

### **Erro: "Cannot connect to Docker daemon"**
```bash
# Iniciar Docker
sudo systemctl start docker

# Adicionar usuário ao grupo docker
sudo usermod -aG docker $USER
# Fazer logout/login
```

### **Frontend não carrega**
```bash
# Verificar logs do Nginx
docker-compose logs frontend

# Verificar se build foi bem-sucedido
docker-compose build frontend --no-cache
```

### **Backend não responde**
```bash
# Verificar logs do Flask
docker-compose logs backend

# Verificar se banco foi criado
docker-compose exec backend ls -la data/

# Testar API diretamente
curl http://localhost:5001/api/health
```

---

## 📊 **MONITORAMENTO**

### **Health Checks**
Os containers têm health checks automáticos:
```bash
# Ver status de saúde
docker-compose ps

# Forçar health check
docker-compose exec backend curl -f http://localhost:5001/api/health
```

### **Logs Estruturados**
```bash
# Logs com timestamp
docker-compose logs -t

# Seguir logs específicos
docker-compose logs -f backend | grep ERROR

# Salvar logs em arquivo
docker-compose logs > bolt_dashboard.log
```

---

## 🔒 **PRODUÇÃO**

### **HTTPS (Recomendado)**
1. Obter certificados SSL
2. Modificar `nginx.conf` para HTTPS
3. Atualizar portas no `docker-compose.yml`

### **Backup Automático**
```bash
# Script de backup (criar backup.sh)
#!/bin/bash
docker-compose exec backend cp /app/data/bolt_dashboard.db /app/data/backup_$(date +%Y%m%d_%H%M%S).db
```

### **Monitoramento Avançado**
Considere adicionar:
- Prometheus + Grafana
- ELK Stack para logs
- Alertas automáticos

---

## ✅ **CHECKLIST DE VERIFICAÇÃO**

Antes de usar em produção:
- [ ] Alterar senhas padrão
- [ ] Configurar HTTPS
- [ ] Implementar backup automático
- [ ] Configurar monitoramento
- [ ] Testar disaster recovery
- [ ] Documentar procedimentos

---

**Criado em:** 30 de Junho de 2025  
**Versão:** 1.0  
**Suporte:** Equipe BOLT Dashboard

