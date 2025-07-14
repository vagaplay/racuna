#!/bin/bash

# Script para parar os servidores do BOLT Dashboard

echo "🛑 Parando BOLT Dashboard..."

# Parar usando PIDs salvos
if [ -f /tmp/bolt_backend.pid ]; then
    BACKEND_PID=$(cat /tmp/bolt_backend.pid)
    if kill -0 $BACKEND_PID 2>/dev/null; then
        echo "🔧 Parando backend (PID: $BACKEND_PID)..."
        kill $BACKEND_PID
    fi
    rm -f /tmp/bolt_backend.pid
fi

if [ -f /tmp/bolt_frontend.pid ]; then
    FRONTEND_PID=$(cat /tmp/bolt_frontend.pid)
    if kill -0 $FRONTEND_PID 2>/dev/null; then
        echo "🎨 Parando frontend (PID: $FRONTEND_PID)..."
        kill $FRONTEND_PID
    fi
    rm -f /tmp/bolt_frontend.pid
fi

# Força parada de processos restantes
echo "🧹 Limpando processos restantes..."
pkill -f "python3 src/main.py" 2>/dev/null || true
pkill -f "npm run dev" 2>/dev/null || true
pkill -f "vite" 2>/dev/null || true

# Aguardar processos terminarem
sleep 3

echo "✅ BOLT Dashboard parado com sucesso!"

