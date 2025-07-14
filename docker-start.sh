#!/bin/bash

# BOLT Dashboard - Script de Inicialização Docker

echo "🚀 Iniciando BOLT Dashboard com Docker..."

# Verificar se Docker está instalado
if ! command -v docker &> /dev/null; then
    echo "❌ Docker não está instalado!"
    echo "📥 Instale o Docker: https://docs.docker.com/get-docker/"
    exit 1
fi

# Verificar se Docker Compose está instalado
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose não está instalado!"
    echo "📥 Instale o Docker Compose: https://docs.docker.com/compose/install/"
    exit 1
fi

# Criar diretórios necessários
echo "📁 Criando diretórios..."
mkdir -p data logs

# Copiar arquivo de ambiente
if [ ! -f .env ]; then
    echo "📋 Copiando arquivo de ambiente..."
    cp .env.docker .env
fi

# Parar containers existentes
echo "🛑 Parando containers existentes..."
docker-compose down

# Limpar imagens antigas (opcional)
read -p "🧹 Deseja limpar imagens antigas? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🧹 Limpando imagens antigas..."
    docker system prune -f
fi

# Build e start dos containers
echo "🔨 Fazendo build dos containers..."
docker-compose build --no-cache

echo "▶️ Iniciando containers..."
docker-compose up -d

# Aguardar containers ficarem prontos
echo "⏳ Aguardando containers ficarem prontos..."
sleep 10

# Verificar status dos containers
echo "📊 Status dos containers:"
docker-compose ps

# Verificar logs do backend
echo "📝 Últimos logs do backend:"
docker-compose logs --tail=10 backend

# Verificar se aplicação está respondendo
echo "🔍 Verificando se aplicação está respondendo..."

# Testar backend
if curl -f http://localhost:5001/api/health &> /dev/null; then
    echo "✅ Backend está funcionando!"
else
    echo "❌ Backend não está respondendo!"
    echo "📝 Logs do backend:"
    docker-compose logs backend
fi

# Testar frontend
if curl -f http://localhost:80 &> /dev/null; then
    echo "✅ Frontend está funcionando!"
else
    echo "❌ Frontend não está respondendo!"
    echo "📝 Logs do frontend:"
    docker-compose logs frontend
fi

echo ""
echo "🎉 BOLT Dashboard iniciado com sucesso!"
echo ""
echo "📱 Acesse a aplicação:"
echo "   Frontend: http://localhost"
echo "   Backend API: http://localhost:5001"
echo ""
echo "🛠️ Comandos úteis:"
echo "   Ver logs: docker-compose logs -f"
echo "   Parar: docker-compose down"
echo "   Reiniciar: docker-compose restart"
echo "   Status: docker-compose ps"
echo ""

