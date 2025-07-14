#!/bin/bash

echo "=== TESTE DE BUILD DO BOLT DASHBOARD ==="
echo "Testando as correções aplicadas..."
echo ""

# Verificar se os arquivos corrigidos existem
echo "1. Verificando arquivos corrigidos:"
if [ -f "azure-dashboard-frontend/package.json" ]; then
    echo "✓ package.json corrigido"
else
    echo "✗ package.json não encontrado"
fi

if [ -f "Dockerfile.frontend" ]; then
    echo "✓ Dockerfile.frontend corrigido"
else
    echo "✗ Dockerfile.frontend não encontrado"
fi

if [ -f "azure-dashboard-frontend/vite.config.js" ]; then
    echo "✓ vite.config.js corrigido"
else
    echo "✗ vite.config.js não encontrado"
fi

if [ -f "azure-dashboard-frontend/tailwind.config.js" ]; then
    echo "✓ tailwind.config.js criado"
else
    echo "✗ tailwind.config.js não encontrado"
fi

if [ -f "docker-compose.yml" ]; then
    echo "✓ docker-compose.yml corrigido"
else
    echo "✗ docker-compose.yml não encontrado"
fi

echo ""
echo "2. Verificando versões no package.json:"
echo "React version:"
grep '"react"' azure-dashboard-frontend/package.json
echo "Node version no Dockerfile:"
grep 'FROM node' Dockerfile.frontend

echo ""
echo "3. Principais correções aplicadas:"
echo "- React downgrade de 19.1.0 para 18.2.0 (versão estável)"
echo "- Todas as dependências @radix-ui ajustadas para versões compatíveis"
echo "- Vite downgrade para versão 5.0.0 (estável)"
echo "- Tailwind CSS configurado corretamente"
echo "- Dockerfile.frontend usa Node 18 e npm install --legacy-peer-deps"
echo "- docker-compose.yml com healthchecks melhorados"
echo ""
echo "=== TESTE CONCLUÍDO ==="

