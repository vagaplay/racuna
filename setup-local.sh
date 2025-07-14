#!/bin/bash

# BOLT Dashboard - Setup Local Melhorado
# Script para configurar o ambiente de desenvolvimento local

set -e

echo "🏠 BOLT Dashboard - Setup Local"
echo "================================"

# Verificar se está no diretório correto
if [ ! -f "README.md" ]; then
    echo "❌ Execute este script na pasta raiz do projeto (azure-dashboard)"
    exit 1
fi

# Verificar Node.js
if ! command -v node &> /dev/null; then
    echo "❌ Node.js não encontrado. Instale em: https://nodejs.org/"
    exit 1
fi

# Verificar Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 não encontrado. Instale em: https://python.org/"
    exit 1
fi

echo "✅ Pré-requisitos verificados"

# Configurar arquivo .env principal
echo ""
echo "🔧 Configurando arquivo de credenciais..."

if [ ! -f ".env" ]; then
    if [ -f ".env.template" ]; then
        echo "📝 Criando .env a partir do template..."
        cp .env.template .env
        echo "✅ Arquivo .env criado!"
        echo ""
        echo "🔑 IMPORTANTE: Edite o arquivo .env e preencha suas credenciais Azure:"
        echo "   - AZURE_TENANT_ID"
        echo "   - AZURE_CLIENT_ID"
        echo "   - AZURE_CLIENT_SECRET"
        echo "   - AZURE_SUBSCRIPTION_ID"
        echo ""
        echo "💡 Como obter credenciais:"
        echo "   az ad sp create-for-rbac --name \"bolt-dashboard-local\""
        echo "   az account show --query id --output tsv"
        echo ""
    else
        echo "❌ Arquivo .env.template não encontrado!"
        exit 1
    fi
else
    echo "✅ Arquivo .env já existe"
fi

# Setup Backend
echo ""
echo "🔧 Configurando Backend..."
cd azure-dashboard-backend

# Criar ambiente virtual se não existir
if [ ! -d "venv" ]; then
    echo "📦 Criando ambiente virtual Python..."
    python3 -m venv venv
fi

# Ativar ambiente virtual
echo "🔄 Ativando ambiente virtual..."
source venv/bin/activate

# Instalar dependências
echo "📦 Instalando dependências Python..."
pip install -r requirements.txt

# Criar arquivo .env do backend se não existir
if [ ! -f ".env" ]; then
    echo "📝 Criando arquivo de configuração backend..."
    cp .env.example .env
    echo "✅ Arquivo backend/.env criado."
fi

# Voltar para raiz
cd ..

# Setup Frontend
echo ""
echo "🎨 Configurando Frontend..."
cd azure-dashboard-frontend

# Instalar dependências
echo "📦 Instalando dependências Node.js..."
npm install

# Instalar dependências de teste
echo "📦 Instalando dependências de teste..."
npm install --save-dev vitest @testing-library/react @testing-library/jest-dom @testing-library/user-event jsdom

# Criar arquivo .env.local do frontend se não existir
if [ ! -f ".env.local" ]; then
    echo "📝 Criando arquivo de configuração frontend..."
    cp .env.example .env.local
    echo "✅ Arquivo frontend/.env.local criado."
fi

# Voltar para raiz
cd ..

# Criar scripts de execução melhorados
echo ""
echo "📜 Criando scripts de execução..."

# Script para iniciar backend
cat > start-backend.sh << 'EOF'
#!/bin/bash
echo "🚀 Iniciando Backend BOLT Dashboard..."

# Verificar se .env existe
if [ ! -f ".env" ]; then
    echo "❌ Arquivo .env não encontrado!"
    echo "Execute: ./setup-local.sh"
    exit 1
fi

# Verificar se credenciais Azure estão configuradas
if ! grep -q "AZURE_TENANT_ID=." .env; then
    echo "⚠️  ATENÇÃO: Credenciais Azure não configuradas!"
    echo "Edite o arquivo .env e preencha suas credenciais Azure"
    echo ""
fi

cd azure-dashboard-backend
source venv/bin/activate

# Copiar .env principal para backend
cp ../.env .env

echo "🔧 Backend rodando em: http://localhost:5000"
python src/main.py
EOF

# Script para iniciar frontend
cat > start-frontend.sh << 'EOF'
#!/bin/bash
echo "🎨 Iniciando Frontend BOLT Dashboard..."

cd azure-dashboard-frontend

echo "🌐 Frontend rodando em: http://localhost:5173"
npm run dev
EOF

# Script para iniciar ambos
cat > start-local.sh << 'EOF'
#!/bin/bash
echo "🚀 Iniciando BOLT Dashboard Completo..."

# Verificar se .env existe
if [ ! -f ".env" ]; then
    echo "❌ Arquivo .env não encontrado!"
    echo "Execute: ./setup-local.sh"
    exit 1
fi

# Verificar se credenciais Azure estão configuradas
if ! grep -q "AZURE_TENANT_ID=." .env; then
    echo "⚠️  ATENÇÃO: Credenciais Azure não configuradas!"
    echo ""
    echo "📝 Para configurar:"
    echo "1. Edite o arquivo .env"
    echo "2. Preencha suas credenciais Azure"
    echo "3. Execute novamente: ./start-local.sh"
    echo ""
    read -p "Continuar mesmo assim? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo "Backend: http://localhost:5000"
echo "Frontend: http://localhost:5173"
echo ""
echo "Pressione Ctrl+C para parar"

# Função para cleanup
cleanup() {
    echo ""
    echo "🛑 Parando servidores..."
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
    exit 0
}

trap cleanup SIGINT

# Iniciar backend em background
cd azure-dashboard-backend
source venv/bin/activate
cp ../.env .env
python src/main.py &
BACKEND_PID=$!

# Aguardar backend inicializar
sleep 3

# Iniciar frontend em background
cd ../azure-dashboard-frontend
npm run dev &
FRONTEND_PID=$!

# Aguardar processos
wait $BACKEND_PID $FRONTEND_PID
EOF

# Script para executar testes
cat > run-tests.sh << 'EOF'
#!/bin/bash
echo "🧪 Executando Testes BOLT Dashboard..."

echo ""
echo "🔧 Testes Backend..."
cd azure-dashboard-backend
source venv/bin/activate
python -m pytest tests/ -v

echo ""
echo "🎨 Testes Frontend..."
cd ../azure-dashboard-frontend
npm test

echo ""
echo "✅ Todos os testes executados!"
EOF

# Tornar scripts executáveis
chmod +x start-backend.sh start-frontend.sh start-local.sh run-tests.sh

echo ""
echo "✅ Setup concluído com sucesso!"
echo ""
echo "📋 Próximos passos:"
echo ""
echo "1. 🔑 Configure suas credenciais Azure:"
echo "   📝 Edite o arquivo: .env"
echo "   🔧 Preencha: AZURE_TENANT_ID, AZURE_CLIENT_ID, AZURE_CLIENT_SECRET, AZURE_SUBSCRIPTION_ID"
echo ""
echo "2. 🚀 Execute o dashboard:"
echo "   ./start-local.sh        # Inicia tudo"
echo "   ./start-backend.sh      # Só backend"
echo "   ./start-frontend.sh     # Só frontend"
echo "   ./run-tests.sh          # Executar testes"
echo ""
echo "3. 🌐 Acesse:"
echo "   Frontend: http://localhost:5173"
echo "   Backend:  http://localhost:5000"
echo ""
echo "💡 Como obter credenciais Azure:"
echo "   az ad sp create-for-rbac --name \"bolt-dashboard-local\""
echo "   az account show --query id --output tsv"
echo ""
echo "🎯 O BOLT Dashboard está pronto para uso local!"

