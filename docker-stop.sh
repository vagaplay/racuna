#!/bin/bash

# BOLT Dashboard - Script para Parar Docker

echo "🛑 Parando BOLT Dashboard..."

# Parar e remover containers
echo "📦 Parando containers..."
docker-compose down

# Verificar se containers foram parados
if [ "$(docker-compose ps -q)" ]; then
    echo "⚠️ Alguns containers ainda estão rodando:"
    docker-compose ps
else
    echo "✅ Todos os containers foram parados!"
fi

# Opção para limpar volumes (dados)
read -p "🗑️ Deseja remover volumes (APAGA DADOS)? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🗑️ Removendo volumes..."
    docker-compose down -v
    echo "⚠️ Dados removidos!"
fi

# Opção para limpar imagens
read -p "🧹 Deseja remover imagens do projeto? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🧹 Removendo imagens..."
    docker-compose down --rmi all
    echo "✅ Imagens removidas!"
fi

echo "✅ BOLT Dashboard parado com sucesso!"

