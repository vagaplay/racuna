#!/bin/bash

# Script para inicializar os servidores do BOLT Dashboard
# Resolve automaticamente problemas de porta e configuração

echo "🚀 Iniciando BOLT Dashboard..."

# Função para matar processos em portas específicas
kill_port() {
    local port=$1
    echo "🔄 Liberando porta $port..."
    lsof -ti:$port | xargs kill -9 2>/dev/null || true
    sleep 2
}

# Função para aguardar que a porta esteja livre
wait_port_free() {
    local port=$1
    local max_attempts=10
    local attempt=0
    
    while lsof -i:$port >/dev/null 2>&1 && [ $attempt -lt $max_attempts ]; do
        echo "⏳ Aguardando porta $port ficar livre... (tentativa $((attempt+1)))"
        sleep 2
        attempt=$((attempt+1))
    done
}

# Parar servidores existentes
echo "🛑 Parando servidores existentes..."
pkill -f "python3 src/main.py" 2>/dev/null || true
pkill -f "npm run dev" 2>/dev/null || true
pkill -f "vite" 2>/dev/null || true

# Aguardar processos terminarem
sleep 3

# Liberar portas específicas
kill_port 5000
kill_port 5174
kill_port 5175
kill_port 5176

# Aguardar portas ficarem livres
wait_port_free 5000
wait_port_free 5175

# Iniciar backend
echo "🔧 Iniciando backend Flask..."
cd /home/ubuntu/azure-dashboard/azure-dashboard-backend
source venv/bin/activate
nohup python3 src/main.py > backend.log 2>&1 &
BACKEND_PID=$!

# Aguardar backend inicializar
echo "⏳ Aguardando backend inicializar..."
sleep 5

# Verificar se backend está rodando
if ! curl -s http://localhost:5000/api/health >/dev/null 2>&1; then
    echo "❌ Erro: Backend não iniciou corretamente"
    cat backend.log
    exit 1
fi

echo "✅ Backend iniciado com sucesso!"

# Iniciar frontend com Vite (SOLUÇÃO DEFINITIVA)
echo "🎨 Iniciando frontend React com Vite..."
cd /home/ubuntu/azure-dashboard/azure-dashboard-frontend

# Limpar cache completamente
echo "🧹 Limpando cache do Vite..."
rm -rf node_modules/.vite 2>/dev/null || true
rm -rf .vite 2>/dev/null || true
rm -rf dist 2>/dev/null || true

# Atualizar .env com nova URL do backend se necessário
BACKEND_URL="http://localhost:5000"
echo "VITE_API_BASE_URL=$BACKEND_URL" > .env.development

# Iniciar Vite com configurações que FORÇAM aceitação de hosts
DANGEROUSLY_DISABLE_HOST_CHECK=true \
VITE_HOST_CHECK=false \
HOST=0.0.0.0 \
nohup npm run dev -- --host 0.0.0.0 --port 5175 --clearScreen false > frontend.log 2>&1 &
FRONTEND_PID=$!

# Aguardar frontend inicializar
echo "⏳ Aguardando frontend inicializar..."
sleep 10

# Verificar se frontend está rodando
FRONTEND_PORT=$(lsof -i -P -n | grep LISTEN | grep node | grep -o ':[0-9]*' | head -1 | cut -d':' -f2)
if [ -z "$FRONTEND_PORT" ]; then
    echo "❌ Erro: Frontend não iniciou corretamente"
    cat frontend.log
    exit 1
fi

echo "✅ Frontend iniciado na porta $FRONTEND_PORT!"

# Salvar PIDs para controle
echo $BACKEND_PID > /tmp/bolt_backend.pid
echo $FRONTEND_PID > /tmp/bolt_frontend.pid

echo ""
echo "🎉 BOLT Dashboard iniciado com sucesso!"
echo "📊 Backend: http://localhost:5000"
echo "🎨 Frontend: http://localhost:$FRONTEND_PORT"
echo ""
echo "📝 Logs:"
echo "   Backend: /home/ubuntu/azure-dashboard/azure-dashboard-backend/backend.log"
echo "   Frontend: /home/ubuntu/azure-dashboard/azure-dashboard-frontend/frontend.log"
echo ""
echo "🛑 Para parar os servidores: ./stop-servers.sh"

