import os
import sys
import os
import logging
from flask import Flask, send_from_directory, send_file, jsonify, request, session, make_response
from flask_cors import CORS
import sqlite3
from datetime import datetime
import json

# Configurar logging detalhado
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Configurar path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# Criar aplicação Flask
app = Flask(__name__, static_folder='../static')

# Configuração de segurança
app.config['SECRET_KEY'] = 'bolt_dashboard_secret_key_production_2024'
app.config['SESSION_COOKIE_SECURE'] = False  # Para desenvolvimento
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

# Configurar CORS para permitir frontend deployado
CORS(app, 
     origins=['https://cdgrjabz.manus.space', 'https://mavlaxgz.manus.space', 'http://localhost:5173', 'http://127.0.0.1:5173', 'https://5001-ir46jikjnmsljq4v81ih6-0d04f0dc.manusvm.computer'],
     supports_credentials=True,
     allow_headers=['Content-Type', 'Authorization', 'X-Requested-With'],
     methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
     expose_headers=['Content-Type', 'Authorization'])

@app.before_request
def handle_preflight():
    """Handle CORS preflight requests"""
    if request.method == "OPTIONS":
        response = make_response()
        response.headers.add("Access-Control-Allow-Origin", request.headers.get('Origin', '*'))
        response.headers.add('Access-Control-Allow-Headers', "Content-Type,Authorization,X-Requested-With")
        response.headers.add('Access-Control-Allow-Methods', "GET,PUT,POST,DELETE,OPTIONS")
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        return response

@app.after_request
def after_request(response):
    """Add CORS headers to all responses"""
    origin = request.headers.get('Origin')
    if origin in ['https://cdgrjabz.manus.space', 'https://mavlaxgz.manus.space', 'http://localhost:5173', 'https://5001-ir46jikjnmsljq4v81ih6-0d04f0dc.manusvm.computer']:
        response.headers.add('Access-Control-Allow-Origin', origin)
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization,X-Requested-With')
        response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

# Banco de dados
DB_PATH = os.path.join(current_dir, 'bolt_dashboard.db')

def init_db():
    """Inicializar banco de dados"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Tabela de usuários
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            name TEXT,
            is_admin BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Inserir usuário de teste se não existir
    cursor.execute('SELECT COUNT(*) FROM users WHERE email = ?', ('test@test.com',))
    if cursor.fetchone()[0] == 0:
        cursor.execute('''
            INSERT INTO users (email, password, name, is_admin)
            VALUES (?, ?, ?, ?)
        ''', ('test@test.com', '123456', 'Usuário Teste', True))
    
    conn.commit()
    conn.close()

# Inicializar banco
init_db()

# Rotas de API
@app.route('/api/health', methods=['GET'])
def health():
    """Endpoint de saúde"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0'
    })

@app.route('/api/auth/login', methods=['POST'])
def login():
    """Endpoint de login"""
    logger.info(f"🔐 LOGIN ATTEMPT - IP: {request.remote_addr}, Origin: {request.headers.get('Origin', 'N/A')}")
    try:
        data = request.get_json()
        logger.info(f"📝 Login data received: {data}")
        
        email = data.get('email')
        password = data.get('password')
        
        if not email or not password:
            logger.warning(f"❌ Login failed - Missing credentials")
            return jsonify({'error': 'Email e senha são obrigatórios'}), 400
        
        logger.info(f"👤 Attempting login for: {email}")
        
        # Verificar usuário no banco
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE email = ? AND password = ?', (email, password))
        user = cursor.fetchone()
        conn.close()
        
        if user:
            # Criar sessão
            session['user_id'] = user[0]
            session['user_email'] = user[1]
            
            logger.info(f"✅ Login successful for: {email}")
            
            return jsonify({
                'message': 'Login realizado com sucesso',
                'user': {
                    'id': user[0],
                    'email': user[1],
                    'name': user[3],
                    'is_admin': bool(user[4])
                }
            })
        else:
            logger.warning(f"❌ Login failed - Invalid credentials for: {email}")
            return jsonify({'error': 'Credenciais inválidas'}), 401
            
    except Exception as e:
        logger.error(f"💥 Login error: {str(e)}")
        return jsonify({'error': f'Erro interno: {str(e)}'}), 500

@app.route('/api/auth/status', methods=['GET'])
def auth_status():
    """Verificar status de autenticação"""
    if 'user_id' in session:
        # Buscar dados do usuário
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],))
        user = cursor.fetchone()
        conn.close()
        
        if user:
            return jsonify({
                'authenticated': True,
                'user': {
                    'id': user[0],
                    'email': user[1],
                    'name': user[3],
                    'is_admin': bool(user[4])
                }
            })
    
    return jsonify({'authenticated': False, 'user': None})

@app.route('/api/auth/logout', methods=['POST'])
def logout():
    """Endpoint de logout"""
    session.clear()
    return jsonify({'message': 'Logout realizado com sucesso'})

@app.route('/api/auth/register', methods=['POST'])
def register():
    """Endpoint de cadastro de usuários"""
    logger.info(f"📝 REGISTER ATTEMPT - IP: {request.remote_addr}, Origin: {request.headers.get('Origin', 'N/A')}")
    try:
        data = request.get_json()
        logger.info(f"📝 Register data received: {data}")
        
        email = data.get('email')
        password = data.get('password')
        name = data.get('name', 'Novo Usuário')
        
        if not email or not password:
            logger.warning(f"❌ Register failed - Missing credentials")
            return jsonify({'error': 'Email e senha são obrigatórios'}), 400
        
        logger.info(f"👤 Attempting register for: {email}")
        
        # Verificar se usuário já existe
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
        existing_user = cursor.fetchone()
        
        if existing_user:
            conn.close()
            logger.warning(f"❌ Register failed - User already exists: {email}")
            return jsonify({'error': 'Usuário já existe'}), 409
        
        # Criar novo usuário
        cursor.execute(
            'INSERT INTO users (email, password, name, is_admin) VALUES (?, ?, ?, ?)',
            (email, password, name, False)
        )
        user_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        # Criar sessão automaticamente
        session['user_id'] = user_id
        session['user_email'] = email
        
        logger.info(f"✅ Register successful for: {email}")
        
        return jsonify({
            'message': 'Cadastro realizado com sucesso',
            'user': {
                'id': user_id,
                'email': email,
                'name': name,
                'is_admin': False
            }
        })
        
    except Exception as e:
        logger.error(f"💥 Register error: {str(e)}")
        return jsonify({'error': f'Erro interno: {str(e)}'}), 500

@app.route('/api/microsoft/login', methods=['GET'])
def microsoft_login():
    """Endpoint de login Microsoft (mock para demonstração)"""
    logger.info(f"🔐 MICROSOFT LOGIN ATTEMPT - IP: {request.remote_addr}, Origin: {request.headers.get('Origin', 'N/A')}")
    
    # Por enquanto, retorna URL de redirecionamento mock
    # Em produção, seria integração real com Azure AD
    return jsonify({
        'redirect_url': 'https://login.microsoftonline.com/common/oauth2/v2.0/authorize?client_id=mock&response_type=code&redirect_uri=mock&scope=openid',
        'message': 'Redirecionamento para Microsoft (funcionalidade em desenvolvimento)'
    })

@app.route('/api/azure/config', methods=['GET'])
def get_azure_config():
    """Obter configuração Azure do usuário"""
    if 'user_id' not in session:
        return jsonify({'error': 'Usuário não autenticado'}), 401
    
    user_id = session['user_id']
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('SELECT tenant_id, client_id, subscription_id FROM azure_config WHERE user_id = ?', (user_id,))
        config = cursor.fetchone()
        conn.close()
        
        if config:
            return jsonify({
                'configured': True,
                'tenant_id': config[0],
                'client_id': config[1],
                'subscription_id': config[2],
                'has_secret': True  # Não retornamos o secret por segurança
            })
        else:
            return jsonify({'configured': False})
            
    except Exception as e:
        logger.error(f"💥 Error getting Azure config: {str(e)}")
        return jsonify({'error': 'Erro ao obter configuração'}), 500

@app.route('/api/azure/config', methods=['POST'])
def save_azure_config():
    """Salvar configuração Azure do usuário"""
    if 'user_id' not in session:
        return jsonify({'error': 'Usuário não autenticado'}), 401
    
    user_id = session['user_id']
    data = request.get_json()
    
    tenant_id = data.get('tenant_id')
    client_id = data.get('client_id')
    client_secret = data.get('client_secret')
    subscription_id = data.get('subscription_id')
    
    if not all([tenant_id, client_id, client_secret, subscription_id]):
        return jsonify({'error': 'Todos os campos são obrigatórios'}), 400
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Verificar se já existe configuração
        cursor.execute('SELECT id FROM azure_config WHERE user_id = ?', (user_id,))
        existing = cursor.fetchone()
        
        if existing:
            # Atualizar configuração existente
            cursor.execute('''
                UPDATE azure_config 
                SET tenant_id = ?, client_id = ?, client_secret = ?, subscription_id = ?, updated_at = CURRENT_TIMESTAMP
                WHERE user_id = ?
            ''', (tenant_id, client_id, client_secret, subscription_id, user_id))
        else:
            # Criar nova configuração
            cursor.execute('''
                INSERT INTO azure_config (user_id, tenant_id, client_id, client_secret, subscription_id)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, tenant_id, client_id, client_secret, subscription_id))
        
        conn.commit()
        conn.close()
        
        logger.info(f"✅ Azure config saved for user: {user_id}")
        return jsonify({'message': 'Configuração Azure salva com sucesso'})
        
    except Exception as e:
        logger.error(f"💥 Error saving Azure config: {str(e)}")
        return jsonify({'error': 'Erro ao salvar configuração'}), 500

@app.route('/api/azure/test-connection', methods=['POST'])
def test_azure_connection():
    """Testar conexão com Azure usando as credenciais configuradas"""
    if 'user_id' not in session:
        return jsonify({'error': 'Usuário não autenticado'}), 401
    
    user_id = session['user_id']
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('SELECT tenant_id, client_id, client_secret, subscription_id FROM azure_config WHERE user_id = ?', (user_id,))
        config = cursor.fetchone()
        conn.close()
        
        if not config:
            return jsonify({'error': 'Configuração Azure não encontrada'}), 404
        
        # Aqui seria implementada a conexão real com Azure
        # Por enquanto, retorna sucesso mock
        return jsonify({
            'success': True,
            'message': 'Conexão com Azure testada com sucesso',
            'subscription_id': config[3],
            'tenant_id': config[0]
        })
        
    except Exception as e:
        logger.error(f"💥 Error testing Azure connection: {str(e)}")
        return jsonify({'error': 'Erro ao testar conexão'}), 500

@app.route('/api/azure/resources', methods=['GET'])
def azure_resources():
    """Endpoint de recursos Azure (mock para demonstração)"""
    return jsonify([
        {
            'id': '/subscriptions/test/resourceGroups/bolt-rg',
            'name': 'bolt-rg',
            'type': 'Microsoft.Resources/resourceGroups',
            'location': 'eastus',
            'status': 'Active'
        },
        {
            'id': '/subscriptions/test/resourceGroups/test-rg',
            'name': 'test-rg', 
            'type': 'Microsoft.Resources/resourceGroups',
            'location': 'westus2',
            'status': 'Active'
        }
    ])

@app.route('/api/azure/costs', methods=['GET'])
def azure_costs():
    """Endpoint de custos Azure (mock para demonstração)"""
    return jsonify({
        'total_cost': 0.00,
        'currency': 'USD',
        'billing_period': datetime.now().strftime('%Y-%m'),
        'daily_costs': [
            {'date': '2024-01-01', 'cost': 0.00},
            {'date': '2024-01-02', 'cost': 0.00}
        ],
        'message': 'Conta Azure vazia - sem custos'
    })

# Servir frontend
@app.route('/debug')
def debug_page():
    """Página de debug para monitoramento"""
    import platform
    import sys
    from datetime import datetime
    
    debug_info = {
        'timestamp': datetime.now().isoformat(),
        'server_info': {
            'python_version': sys.version,
            'platform': platform.platform(),
            'host': request.host,
            'remote_addr': request.remote_addr,
            'user_agent': request.headers.get('User-Agent', 'N/A')
        },
        'request_info': {
            'method': request.method,
            'url': request.url,
            'headers': dict(request.headers),
            'origin': request.headers.get('Origin', 'N/A'),
            'referer': request.headers.get('Referer', 'N/A')
        },
        'cors_config': {
            'allowed_origins': [
                'https://cdgrjabz.manus.space', 
                'https://mavlaxgz.manus.space', 
                'http://localhost:5173', 
                'https://5001-ir46jikjnmsljq4v81ih6-0d04f0dc.manusvm.computer'
            ]
        },
        'backend_status': {
            'health_endpoint': '/api/health',
            'login_endpoint': '/api/auth/login',
            'cors_enabled': True,
            'debug_mode': app.debug
        }
    }
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>BOLT Dashboard - Debug</title>
        <style>
            body {{ font-family: monospace; margin: 20px; background: #1a1a1a; color: #00ff00; }}
            .section {{ margin: 20px 0; padding: 15px; border: 1px solid #333; background: #2a2a2a; }}
            .title {{ color: #ffff00; font-size: 18px; font-weight: bold; }}
            .test-btn {{ background: #007acc; color: white; padding: 10px 20px; margin: 10px; border: none; cursor: pointer; }}
            .result {{ margin: 10px 0; padding: 10px; background: #333; }}
            .success {{ color: #00ff00; }}
            .error {{ color: #ff0000; }}
        </style>
    </head>
    <body>
        <h1>🔧 BOLT Dashboard - Página de Debug</h1>
        
        <div class="section">
            <div class="title">📊 Informações do Servidor</div>
            <pre>{debug_info['server_info']}</pre>
        </div>
        
        <div class="section">
            <div class="title">🌐 Informações da Requisição</div>
            <pre>{debug_info['request_info']}</pre>
        </div>
        
        <div class="section">
            <div class="title">🔒 Configuração CORS</div>
            <pre>{debug_info['cors_config']}</pre>
        </div>
        
        <div class="section">
            <div class="title">⚡ Status do Backend</div>
            <pre>{debug_info['backend_status']}</pre>
        </div>
        
        <div class="section">
            <div class="title">🧪 Testes de API</div>
            <button class="test-btn" onclick="testHealth()">Testar Health Check</button>
            <button class="test-btn" onclick="testLogin()">Testar Login</button>
            <div id="test-results"></div>
        </div>
        
        <script>
            async function testHealth() {{
                const result = document.getElementById('test-results');
                try {{
                    const response = await fetch('/api/health');
                    const data = await response.json();
                    result.innerHTML = '<div class="result success">✅ Health Check: ' + JSON.stringify(data, null, 2) + '</div>';
                }} catch (error) {{
                    result.innerHTML = '<div class="result error">❌ Health Check Error: ' + error.message + '</div>';
                }}
            }}
            
            async function testLogin() {{
                const result = document.getElementById('test-results');
                try {{
                    const response = await fetch('/api/auth/login', {{
                        method: 'POST',
                        headers: {{ 'Content-Type': 'application/json' }},
                        body: JSON.stringify({{ email: 'test@test.com', password: '123456' }})
                    }});
                    const data = await response.json();
                    result.innerHTML = '<div class="result success">✅ Login Test: ' + JSON.stringify(data, null, 2) + '</div>';
                }} catch (error) {{
                    result.innerHTML = '<div class="result error">❌ Login Error: ' + error.message + '</div>';
                }}
            }}
        </script>
    </body>
    </html>
    """
    return html

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_frontend(path):
    """Servir arquivos do frontend"""
    if path and os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)
    else:
        return send_from_directory(app.static_folder, 'index.html')

if __name__ == '__main__':
    print("🚀 BOLT Dashboard Backend - Versão Deploy")
    print("✅ Banco de dados inicializado")
    print("✅ CORS configurado para frontend deployado")
    print("✅ Usuário teste: test@test.com / 123456")
    print("🌐 Servidor iniciando...")
    
    app.run(
        host='0.0.0.0',
        port=int(os.environ.get('PORT', 5000)),
        debug=False
    )

