# =============================================================================
# DOCKERFILE PARA BOLT DASHBOARD - CONTAINERIZAÇÃO DO PROJETO EXISTENTE
# =============================================================================
# Este Dockerfile containeriza o projeto BOLT Dashboard existente, resolvendo:
# ✅ Comunicação frontend ↔ backend (nginx reverse proxy)
# ✅ Conflitos de dependências (isolamento)
# ✅ Deploy consistente
# ✅ Mantém todas as funcionalidades existentes

# =============================================================================
# STAGE 1: BUILD FRONTEND (React)
# =============================================================================
FROM node:18-alpine AS frontend-builder

WORKDIR /app/frontend

# Copiar package.json e instalar dependências
COPY azure-dashboard-frontend/package*.json ./
RUN npm ci --only=production

# Copiar código fonte e fazer build
COPY azure-dashboard-frontend/ ./
RUN npm run build

# =============================================================================
# STAGE 2: PREPARAR BACKEND (Python Flask)
# =============================================================================
FROM python:3.11-slim AS backend-builder

WORKDIR /app/backend

# Instalar dependências do sistema para Azure SDK
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libffi-dev \
    libssl-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements e instalar dependências
COPY azure-dashboard-backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código do backend
COPY azure-dashboard-backend/ ./

# =============================================================================
# STAGE 3: RUNTIME - NGINX + PYTHON (Produção)
# =============================================================================
FROM python:3.11-slim AS production

# Instalar nginx, supervisor e dependências runtime
RUN apt-get update && apt-get install -y \
    nginx \
    supervisor \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Criar usuário não-root
RUN useradd --create-home --shell /bin/bash app

# Configurar diretórios
WORKDIR /app
RUN mkdir -p /app/frontend /app/backend /app/data /var/log/supervisor

# Copiar frontend buildado
COPY --from=frontend-builder /app/frontend/dist /app/frontend/

# Copiar backend e dependências Python
COPY --from=backend-builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=backend-builder /app/backend /app/backend/

# =============================================================================
# CONFIGURAÇÃO NGINX - RESOLVE COMUNICAÇÃO FRONTEND ↔ BACKEND
# =============================================================================
RUN cat > /etc/nginx/sites-available/default << 'EOF'
server {
    listen 80;
    server_name _;
    client_max_body_size 50M;

    # Frontend (React) - Servir arquivos estáticos
    location / {
        root /app/frontend;
        try_files $uri $uri/ /index.html;
        
        # Headers para SPA
        add_header Cache-Control "no-cache, no-store, must-revalidate";
        add_header Pragma "no-cache";
        add_header Expires "0";
    }

    # Backend (Flask) - Proxy para APIs
    location /api/ {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # CORS headers
        add_header Access-Control-Allow-Origin *;
        add_header Access-Control-Allow-Methods "GET, POST, PUT, DELETE, OPTIONS";
        add_header Access-Control-Allow-Headers "Content-Type, Authorization";
        
        # Handle preflight requests
        if ($request_method = 'OPTIONS') {
            add_header Access-Control-Allow-Origin *;
            add_header Access-Control-Allow-Methods "GET, POST, PUT, DELETE, OPTIONS";
            add_header Access-Control-Allow-Headers "Content-Type, Authorization";
            return 204;
        }
    }

    # Health check
    location /health {
        proxy_pass http://127.0.0.1:5000/api/health;
        access_log off;
    }

    # Static assets com cache
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
        root /app/frontend;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
EOF

# =============================================================================
# CONFIGURAÇÃO SUPERVISOR - GERENCIAR PROCESSOS
# =============================================================================
RUN cat > /etc/supervisor/conf.d/supervisord.conf << 'EOF'
[supervisord]
nodaemon=true
user=root
logfile=/var/log/supervisor/supervisord.log
pidfile=/var/run/supervisord.pid

[program:nginx]
command=nginx -g "daemon off;"
autostart=true
autorestart=true
stderr_logfile=/var/log/supervisor/nginx.err.log
stdout_logfile=/var/log/supervisor/nginx.out.log

[program:flask]
command=python /app/backend/src/main.py
directory=/app/backend
autostart=true
autorestart=true
user=app
environment=PYTHONPATH="/app/backend",FLASK_ENV="production"
stderr_logfile=/var/log/supervisor/flask.err.log
stdout_logfile=/var/log/supervisor/flask.out.log
EOF

# =============================================================================
# SCRIPT DE INICIALIZAÇÃO
# =============================================================================
RUN cat > /app/start.sh << 'EOF'
#!/bin/bash

# Inicializar banco de dados se não existir
if [ ! -f /app/data/bolt_dashboard.db ]; then
    echo "Inicializando banco de dados..."
    cd /app/backend
    python init_db.py
fi

# Configurar permissões
chown -R app:app /app/data
chmod 755 /app/data

# Iniciar supervisor
exec /usr/bin/supervisord -c /etc/supervisor/conf.d/supervisord.conf
EOF

RUN chmod +x /app/start.sh

# =============================================================================
# CONFIGURAÇÕES FINAIS
# =============================================================================

# Configurar permissões
RUN chown -R app:app /app/data

# Variáveis de ambiente
ENV FLASK_ENV=production
ENV PYTHONPATH=/app/backend
ENV DATABASE_PATH=/app/data/bolt_dashboard.db

# Volume para dados persistentes
VOLUME ["/app/data"]

# Expor porta 80
EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost/health || exit 1

# Comando de inicialização
CMD ["/app/start.sh"]

# =============================================================================
# INSTRUÇÕES DE USO
# =============================================================================
# 
# BUILD:
# docker build -t bolt-dashboard .
#
# RUN LOCAL:
# docker run -p 8080:80 \
#   -e AZURE_TENANT_ID=seu_tenant_id \
#   -e AZURE_CLIENT_ID=seu_client_id \
#   -e AZURE_CLIENT_SECRET=seu_client_secret \
#   -e AZURE_SUBSCRIPTION_ID=seu_subscription_id \
#   -v bolt_data:/app/data \
#   bolt-dashboard
#
# ACESSO:
# http://localhost:8080
#
# =============================================================================

