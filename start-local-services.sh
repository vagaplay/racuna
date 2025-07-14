#!/bin/bash

# Script para iniciar serviços locais do dashboard

echo "Iniciando serviços do BOLT Dashboard..."

# Parar processos existentes
echo "Parando processos existentes..."
pkill -f "main.py" 2>/dev/null || true
pkill -f "vite" 2>/dev/null || true
sleep 2

# Iniciar backend
echo "Iniciando backend na porta 5001..."
cd azure-dashboard-backend/src
python3 main.py &
BACKEND_PID=$!
cd ../..

# Aguardar backend inicializar
echo "Aguardando backend inicializar..."
sleep 5

# Verificar se backend está funcionando
if curl -f http://localhost:5001/api/health >/dev/null 2>&1; then
    echo "✓ Backend funcionando na porta 5001"
else
    echo "✗ Erro: Backend não está respondendo"
    exit 1
fi

# Iniciar frontend
echo "Iniciando frontend..."
cd azure-dashboard-frontend
npm run dev &
FRONTEND_PID=$!
cd ..

echo "Serviços iniciados:"
echo "- Backend: http://localhost:5001"
echo "- Frontend: http://localhost:5174"
echo ""
echo "PIDs: Backend=$BACKEND_PID, Frontend=$FRONTEND_PID"
echo ""
echo "Para parar os serviços, execute:"
echo "kill $BACKEND_PID $FRONTEND_PID"

