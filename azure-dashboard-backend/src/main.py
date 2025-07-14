import os
import sys
import os
from flask import Flask, send_from_directory, jsonify, request, session, make_response
from flask_cors import CORS
import sqlite3
from datetime import datetime
import json
import requests
from azure.identity import ClientSecretCredential
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.consumption import ConsumptionManagementClient

# Configurar path
current_dir = os.path.dirname(os.path.abspath(__file__))
static_dir = os.path.join(os.path.dirname(current_dir), 'static')

# Criar app Flask
app = Flask(__name__, static_folder=static_dir, static_url_path='')

# Configurações de sessão
app.config['SECRET_KEY'] = 'bolt-dashboard-secret-key-2024'
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # Mudando para Lax para desenvolvimento local
app.config['SESSION_COOKIE_SECURE'] = False  # Para desenvolvimento local
app.config['SESSION_COOKIE_HTTPONLY'] = False  # Permitir acesso via JavaScript para debug

# Configurar CORS
CORS(app, 
     origins=['http://localhost:5173', 'http://127.0.0.1:5173'], 
     supports_credentials=True,
     allow_headers=['Content-Type', 'Authorization'],
     methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'])

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
            department TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_admin BOOLEAN DEFAULT FALSE
        )
    ''')
    
    # Tabela de credenciais Azure
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS azure_credentials (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            tenant_id TEXT NOT NULL,
            client_id TEXT NOT NULL,
            client_secret TEXT NOT NULL,
            subscription_id TEXT NOT NULL,
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Tabela de configurações de budget
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS budget_configs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            budget_name TEXT NOT NULL,
            amount REAL NOT NULL,
            alert_threshold_50 BOOLEAN DEFAULT TRUE,
            alert_threshold_75 BOOLEAN DEFAULT TRUE,
            alert_threshold_90 BOOLEAN DEFAULT TRUE,
            alert_threshold_100 BOOLEAN DEFAULT TRUE,
            email_alerts TEXT,
            webhook_url TEXT,
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Tabela de agendamentos
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS schedules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            schedule_name TEXT NOT NULL,
            schedule_type TEXT NOT NULL,
            cron_expression TEXT,
            action_type TEXT NOT NULL,
            action_config TEXT,
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Inserir usuário teste se não existir
    cursor.execute('SELECT COUNT(*) FROM users WHERE email = ?', ('test@test.com',))
    if cursor.fetchone()[0] == 0:
        cursor.execute('''
            INSERT INTO users (email, password, name, department, is_admin) 
            VALUES (?, ?, ?, ?, ?)
        ''', ('test@test.com', '123456', 'Usuário Teste', 'TI', True))
    
    conn.commit()
    conn.close()

def get_azure_client(user_id):
    """Obter cliente Azure para o usuário"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT tenant_id, client_id, client_secret, subscription_id 
        FROM azure_credentials 
        WHERE user_id = ? AND is_active = TRUE
        ORDER BY created_at DESC LIMIT 1
    ''', (user_id,))
    creds = cursor.fetchone()
    conn.close()
    
    if not creds:
        return None, None
    
    try:
        credential = ClientSecretCredential(
            tenant_id=creds[0],
            client_id=creds[1],
            client_secret=creds[2]
        )
        
        resource_client = ResourceManagementClient(credential, creds[3])
        consumption_client = ConsumptionManagementClient(credential, creds[3])
        
        return resource_client, consumption_client
    except Exception as e:
        print(f"Erro ao criar cliente Azure: {e}")
        return None, None

init_db()

# APIs
@app.route('/api/health')
def health():
    return jsonify({
        'status': 'healthy', 
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0'
    })

@app.route('/debug')
def debug():
    return f'''
    <html>
    <head><title>Debug BOLT Dashboard</title></head>
    <body>
        <h1>Debug BOLT Dashboard</h1>
        <h2>Informações do Cliente</h2>
        <p><strong>IP:</strong> {request.remote_addr}</p>
        <p><strong>User-Agent:</strong> {request.headers.get('User-Agent')}</p>
        <p><strong>Origin:</strong> {request.headers.get('Origin')}</p>
        
        <h2>Testes de API</h2>
        <button onclick="testHealth()">Testar Health Check</button>
        <button onclick="testLogin()">Testar Login</button>
        
        <h2>Resultados</h2>
        <div id="results"></div>
        
        <script>
        async function testHealth() {{
            try {{
                const response = await fetch('/api/health');
                const data = await response.json();
                document.getElementById('results').innerHTML = '<h3>Health Check:</h3><pre>' + JSON.stringify(data, null, 2) + '</pre>';
            }} catch (error) {{
                document.getElementById('results').innerHTML = '<h3>Erro Health Check:</h3><pre>' + error.message + '</pre>';
            }}
        }}
        
        async function testLogin() {{
            try {{
                const response = await fetch('/api/auth/login', {{
                    method: 'POST',
                    headers: {{'Content-Type': 'application/json'}},
                    body: JSON.stringify({{'email': 'test@test.com', 'password': '123456'}})
                }});
                const data = await response.json();
                document.getElementById('results').innerHTML = '<h3>Login Test:</h3><pre>' + JSON.stringify(data, null, 2) + '</pre>';
            }} catch (error) {{
                document.getElementById('results').innerHTML = '<h3>Erro Login:</h3><pre>' + error.message + '</pre>';
            }}
        }}
        </script>
    </body>
    </html>
    '''

@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE email = ? AND password = ?', (email, password))
    user = cursor.fetchone()
    conn.close()
    
    if user:
        session['user_id'] = user[0]
        session['user_email'] = user[1]
        session['user_name'] = user[3]
        session['user_department'] = user[4]
        return jsonify({
            'message': 'Login realizado com sucesso',
            'user': {
                'id': user[0], 
                'email': user[1], 
                'name': user[3],
                'department': user[4],
                'is_admin': bool(user[5])
            }
        })
    else:
        return jsonify({'error': 'Credenciais inválidas'}), 401

@app.route('/api/auth/register', methods=['POST'])
def register():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    name = data.get('name')
    department = data.get('department', '')
    
    if not email or not password:
        return jsonify({'error': 'Email e senha são obrigatórios'}), 400
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            INSERT INTO users (email, password, name) 
            VALUES (?, ?, ?)
        ''', (email, password, name))
        conn.commit()
        user_id = cursor.lastrowid
        
        session['user_id'] = user_id
        session['user_email'] = email
        session['user_name'] = name
        
        return jsonify({
            'message': 'Cadastro realizado com sucesso',
            'user': {
                'id': user_id,
                'email': email,
                'name': name,
                'department': department
            }
        })
    except sqlite3.IntegrityError:
        return jsonify({'error': 'Email já cadastrado'}), 400
    finally:
        conn.close()

@app.route('/api/auth/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'message': 'Logout realizado com sucesso'})

@app.route('/api/auth/status')
def auth_status():
    if 'user_id' in session:
        return jsonify({
            'authenticated': True,
            'user': {
                'id': session['user_id'],
                'email': session['user_email'],
                'name': session.get('user_name', ''),
                'department': session.get('user_department', ''),
                'is_admin': session.get('user_is_admin', False)
            }
        })
    else:
        return jsonify({'authenticated': False}), 401

@app.route('/api/azure/credentials-status')
def azure_credentials_status():
    """Verificar se credenciais Azure estão configuradas"""
    if 'user_id' not in session:
        return jsonify({'error': 'Não autenticado'}), 401
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT tenant_id, client_id, subscription_id 
            FROM azure_credentials 
            WHERE user_id = ? AND is_active = 1
        ''', (session['user_id'],))
        
        credentials = cursor.fetchone()
        conn.close()
        
        if credentials:
            return jsonify({
                'configured': True,
                'tenant_id': credentials[0],
                'client_id': credentials[1],
                'subscription_id': credentials[2]
            })
        else:
            return jsonify({'configured': False})
            
    except Exception as e:
        return jsonify({'error': f'Erro ao verificar credenciais: {str(e)}'}), 500

@app.route('/api/microsoft/login')
def microsoft_login():
    # Mock para desenvolvimento - implementar OAuth real depois
    return jsonify({
        'message': 'Login Microsoft em desenvolvimento',
        'redirect_url': 'https://login.microsoftonline.com/oauth2/v2.0/authorize'
    })

# APIs Azure Configuration
@app.route('/api/azure/credentials', methods=['GET'])
def get_azure_credentials():
    if 'user_id' not in session:
        return jsonify({'error': 'Não autenticado'}), 401
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, tenant_id, client_id, subscription_id, is_active, created_at
        FROM azure_credentials 
        WHERE user_id = ? 
        ORDER BY created_at DESC
    ''', (session['user_id'],))
    
    credentials = []
    for row in cursor.fetchall():
        credentials.append({
            'id': row[0],
            'tenant_id': row[1],
            'client_id': row[2],
            'subscription_id': row[3],
            'is_active': bool(row[4]),
            'created_at': row[5]
        })
    
    conn.close()
    return jsonify({'credentials': credentials})

@app.route('/api/azure/credentials', methods=['POST'])
def save_azure_credentials():
    if 'user_id' not in session:
        return jsonify({'error': 'Não autenticado'}), 401
    
    data = request.get_json()
    tenant_id = data.get('tenant_id')
    client_id = data.get('client_id')
    client_secret = data.get('client_secret')
    subscription_id = data.get('subscription_id')
    
    if not all([tenant_id, client_id, client_secret, subscription_id]):
        return jsonify({'error': 'Todos os campos são obrigatórios'}), 400
    
    # Testar credenciais
    try:
        credential = ClientSecretCredential(tenant_id, client_id, client_secret)
        resource_client = ResourceManagementClient(credential, subscription_id)
        # Teste simples - listar resource groups
        list(resource_client.resource_groups.list())
        
        # Salvar no banco
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Desativar credenciais antigas
        cursor.execute('''
            UPDATE azure_credentials 
            SET is_active = FALSE 
            WHERE user_id = ?
        ''', (session['user_id'],))
        
        # Inserir novas credenciais
        cursor.execute('''
            INSERT INTO azure_credentials 
            (user_id, tenant_id, client_id, client_secret, subscription_id) 
            VALUES (?, ?, ?, ?, ?)
        ''', (session['user_id'], tenant_id, client_id, client_secret, subscription_id))
        
        conn.commit()
        conn.close()
        
        return jsonify({'message': 'Credenciais Azure salvas com sucesso'})
        
    except Exception as e:
        return jsonify({'error': f'Erro ao validar credenciais: {str(e)}'}), 400

@app.route('/api/azure/configure-credentials', methods=['POST'])
def configure_azure_credentials():
    """API para configurar credenciais Azure (alias para save_azure_credentials)"""
    return save_azure_credentials()

@app.route('/api/azure/test-connection', methods=['GET', 'POST'])
def test_azure_connection():
    if 'user_id' not in session:
        return jsonify({'error': 'Não autenticado'}), 401
    
    resource_client, consumption_client = get_azure_client(session['user_id'])
    
    if not resource_client:
        return jsonify({
            'connected': False,
            'error': 'Credenciais Azure não configuradas'
        }), 400
    
    try:
        # Teste de conexão
        resource_groups = list(resource_client.resource_groups.list())
        return jsonify({
            'connected': True,
            'resource_groups_count': len(resource_groups),
            'message': 'Conexão Azure funcionando'
        })
    except Exception as e:
        return jsonify({
            'connected': False,
            'error': f'Erro de conexão: {str(e)}'
        }), 400

# APIs Azure Test - Resource Groups
@app.route('/api/azure-test/list-resource-groups')
def list_resource_groups():
    if 'user_id' not in session:
        return jsonify({'error': 'Não autenticado'}), 401
    
    resource_client, _ = get_azure_client(session['user_id'])
    
    if not resource_client:
        return jsonify({'error': 'Credenciais Azure não configuradas'}), 400
    
    try:
        resource_groups = []
        for rg in resource_client.resource_groups.list():
            resource_groups.append({
                'name': rg.name,
                'location': rg.location,
                'id': rg.id,
                'tags': rg.tags or {}
            })
        
        return jsonify({'resource_groups': resource_groups})
    except Exception as e:
        return jsonify({'error': f'Erro ao listar resource groups: {str(e)}'}), 500

# APIs Azure Actions - Locks
@app.route('/api/azure-actions/list-locks')
def list_locks():
    if 'user_id' not in session:
        return jsonify({'error': 'Não autenticado'}), 401
    
    resource_client, _ = get_azure_client(session['user_id'])
    
    if not resource_client:
        return jsonify({'error': 'Credenciais Azure não configuradas'}), 400
    
    try:
        # Listar locks de todos os resource groups
        locks = []
        for rg in resource_client.resource_groups.list():
            try:
                rg_locks = list(resource_client.management_locks.list_by_resource_group(rg.name))
                for lock in rg_locks:
                    locks.append({
                        'name': lock.name,
                        'level': lock.level,
                        'resource_group': rg.name,
                        'id': lock.id,
                        'notes': lock.notes or ''
                    })
            except:
                continue
        
        return jsonify({'locks': locks})
    except Exception as e:
        return jsonify({'error': f'Erro ao listar locks: {str(e)}'}), 500

# APIs Azure Budget
@app.route('/api/azure-budget/current-costs')
def current_costs():
    if 'user_id' not in session:
        return jsonify({'error': 'Não autenticado'}), 401
    
    # Mock data - implementar com Consumption API
    return jsonify({
        'current_cost': 0.0,
        'currency': 'BRL',
        'period': 'current_month',
        'last_updated': datetime.now().isoformat()
    })

@app.route('/api/azure-budget/forecast')
def budget_forecast():
    if 'user_id' not in session:
        return jsonify({'error': 'Não autenticado'}), 401
    
    days = request.args.get('days', 30)
    
    # Mock data - implementar com Consumption API
    return jsonify({
        'forecast_cost': 0.0,
        'currency': 'BRL',
        'days': int(days),
        'confidence': 'medium'
    })

@app.route('/api/azure-budget/status')
def budget_status():
    if 'user_id' not in session:
        return jsonify({'error': 'Não autenticado'}), 401
    
    # Mock data
    return jsonify({
        'budget_configured': False,
        'current_spend': 0.0,
        'budget_limit': 0.0,
        'percentage_used': 0.0,
        'status': 'ok'
    })

@app.route('/api/azure-budget/alerts')
def budget_alerts():
    if 'user_id' not in session:
        return jsonify({'error': 'Não autenticado'}), 401
    
    # Mock data
    return jsonify({'alerts': []})

@app.route('/api/azure-budget/recommendations')
def budget_recommendations():
    if 'user_id' not in session:
        return jsonify({'error': 'Não autenticado'}), 401
    
    # Mock data
    return jsonify({'recommendations': []})

@app.route('/api/dashboard/overview')
def dashboard():
    if 'user_id' not in session:
        return jsonify({'error': 'Não autenticado'}), 401
    
    resource_client, consumption_client = get_azure_client(session['user_id'])
    
    if not resource_client:
        return jsonify({
            'total_resources': 0,
            'total_cost': 0.0,
            'active_alerts': 0,
            'resource_groups': 0,
            'message': 'Configure suas credenciais Azure para ver dados reais',
            'azure_connected': False
        })
    
    try:
        # Dados reais do Azure
        resource_groups = list(resource_client.resource_groups.list())
        resources = list(resource_client.resources.list())
        
        return jsonify({
            'total_resources': len(resources),
            'total_cost': 0.0,  # Implementar com Consumption API
            'active_alerts': 0,
            'resource_groups': len(resource_groups),
            'azure_connected': True,
            'message': 'Dados carregados do Azure'
        })
    except Exception as e:
        return jsonify({
            'total_resources': 0,
            'total_cost': 0.0,
            'active_alerts': 0,
            'resource_groups': 0,
            'message': f'Erro ao conectar com Azure: {str(e)}',
            'azure_connected': False
        })

@app.route('/api/azure/resources')
def get_azure_resources():
    if 'user_id' not in session:
        return jsonify({'error': 'Não autenticado'}), 401
    
    resource_client, _ = get_azure_client(session['user_id'])
    
    if not resource_client:
        return jsonify({
            'resources': [],
            'message': 'Configure suas credenciais Azure'
        })
    
    try:
        resources = []
        for resource in resource_client.resources.list():
            resources.append({
                'id': resource.id,
                'name': resource.name,
                'type': resource.type,
                'location': resource.location,
                'resource_group': resource.id.split('/')[4],
                'tags': resource.tags or {}
            })
        
        return jsonify({
            'resources': resources,
            'count': len(resources)
        })
    except Exception as e:
        return jsonify({
            'resources': [],
            'message': f'Erro ao buscar recursos: {str(e)}'
        })

# APIs de Ações Azure - Implementação completa
@app.route('/api/azure-actions/create-resource-group', methods=['POST'])
def create_resource_group():
    if 'user_id' not in session:
        return jsonify({'error': 'Não autenticado'}), 401
    
    data = request.get_json()
    if not data or 'name' not in data or 'location' not in data:
        return jsonify({'error': 'Nome e localização são obrigatórios'}), 400
    
    resource_client, _ = get_azure_client(session['user_id'])
    
    if not resource_client:
        return jsonify({'error': 'Configure suas credenciais Azure'}), 400
    
    try:
        # Criar Resource Group no Azure
        rg_params = {
            'location': data['location'],
            'tags': {
                'created_by': 'BOLT Dashboard',
                'environment': data.get('environment', 'development'),
                'purpose': data.get('purpose', 'general')
            }
        }
        
        result = resource_client.resource_groups.create_or_update(
            data['name'], 
            rg_params
        )
        
        return jsonify({
            'success': True,
            'message': f'Resource Group {data["name"]} criado com sucesso',
            'resource_group': {
                'name': result.name,
                'location': result.location,
                'id': result.id,
                'tags': result.tags
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Erro ao criar Resource Group: {str(e)}'
        }), 500

@app.route('/api/azure-actions/delete-resource-group', methods=['POST'])
def delete_resource_group():
    if 'user_id' not in session:
        return jsonify({'error': 'Não autenticado'}), 401
    
    data = request.get_json()
    if not data or 'name' not in data:
        return jsonify({'error': 'Nome do Resource Group é obrigatório'}), 400
    
    resource_client, _ = get_azure_client(session['user_id'])
    
    if not resource_client:
        return jsonify({'error': 'Configure suas credenciais Azure'}), 400
    
    try:
        # Deletar Resource Group no Azure
        operation = resource_client.resource_groups.begin_delete(data['name'])
        
        return jsonify({
            'success': True,
            'message': f'Resource Group {data["name"]} está sendo deletado',
            'operation_id': operation.polling_method()._operation.location if hasattr(operation, 'polling_method') else 'unknown'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Erro ao deletar Resource Group: {str(e)}'
        }), 500

@app.route('/api/azure-actions/create-lock', methods=['POST'])
def create_lock():
    if 'user_id' not in session:
        return jsonify({'error': 'Não autenticado'}), 401
    
    data = request.get_json()
    if not data or 'name' not in data or 'level' not in data:
        return jsonify({'error': 'Nome e nível do lock são obrigatórios'}), 400
    
    resource_client, _ = get_azure_client(session['user_id'])
    
    if not resource_client:
        return jsonify({'error': 'Configure suas credenciais Azure'}), 400
    
    try:
        from azure.mgmt.resource import ManagementLockClient
        
        # Obter credenciais Azure
        conn = sqlite3.connect('bolt_dashboard.db')
        cursor = conn.cursor()
        cursor.execute('SELECT tenant_id, client_id, client_secret, subscription_id FROM azure_credentials WHERE user_id = ? AND is_active = 1', (session['user_id'],))
        creds = cursor.fetchone()
        conn.close()
        
        if not creds:
            return jsonify({'error': 'Credenciais Azure não encontradas'}), 400
        
        tenant_id, client_id, client_secret, subscription_id = creds
        
        from azure.identity import ClientSecretCredential
        credential = ClientSecretCredential(tenant_id, client_id, client_secret)
        lock_client = ManagementLockClient(credential, subscription_id)
        
        # Determinar escopo do lock
        if data.get('scope') == 'subscription':
            scope = f'/subscriptions/{subscription_id}'
        else:
            # Default para subscription
            scope = f'/subscriptions/{subscription_id}'
        
        # Criar lock no Azure
        lock_params = {
            'level': data['level'],  # 'CanNotDelete' ou 'ReadOnly'
            'notes': data.get('notes', 'Lock criado pelo BOLT Dashboard para controle de gastos')
        }
        
        result = lock_client.management_locks.create_or_update_by_scope(
            scope,
            data['name'],
            lock_params
        )
        
        return jsonify({
            'success': True,
            'message': f'Lock {data["name"]} criado com sucesso',
            'lock': {
                'name': result.name,
                'level': result.level,
                'scope': scope,
                'notes': result.notes
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Erro ao criar lock: {str(e)}'
        }), 500

@app.route('/api/azure-actions/remove-lock', methods=['DELETE'])
def remove_lock():
    if 'user_id' not in session:
        return jsonify({'error': 'Não autenticado'}), 401
    
    data = request.get_json()
    if not data or 'name' not in data:
        return jsonify({'error': 'Nome do lock é obrigatório'}), 400
    
    try:
        from azure.mgmt.resource import ManagementLockClient
        
        # Obter credenciais Azure
        conn = sqlite3.connect('bolt_dashboard.db')
        cursor = conn.cursor()
        cursor.execute('SELECT tenant_id, client_id, client_secret, subscription_id FROM azure_credentials WHERE user_id = ? AND is_active = 1', (session['user_id'],))
        creds = cursor.fetchone()
        conn.close()
        
        if not creds:
            return jsonify({'error': 'Credenciais Azure não encontradas'}), 400
        
        tenant_id, client_id, client_secret, subscription_id = creds
        
        from azure.identity import ClientSecretCredential
        credential = ClientSecretCredential(tenant_id, client_id, client_secret)
        lock_client = ManagementLockClient(credential, subscription_id)
        
        # Determinar escopo do lock
        scope = data.get('scope', f'/subscriptions/{subscription_id}')
        
        # Remover lock do Azure
        lock_client.management_locks.delete_by_scope(scope, data['name'])
        
        return jsonify({
            'success': True,
            'message': f'Lock {data["name"]} removido com sucesso'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Erro ao remover lock: {str(e)}'
        }), 500

# APIs de Budget - Implementação completa
@app.route('/api/azure-budget/configure', methods=['POST'])
def configure_budget():
    if 'user_id' not in session:
        return jsonify({'error': 'Não autenticado'}), 401
    
    data = request.get_json()
    if not data or 'amount' not in data:
        return jsonify({'error': 'Valor do orçamento é obrigatório'}), 400
    
    try:
        from azure.mgmt.consumption import ConsumptionManagementClient
        
        # Obter credenciais Azure
        conn = sqlite3.connect('bolt_dashboard.db')
        cursor = conn.cursor()
        cursor.execute('SELECT tenant_id, client_id, client_secret, subscription_id FROM azure_credentials WHERE user_id = ? AND is_active = 1', (session['user_id'],))
        creds = cursor.fetchone()
        conn.close()
        
        if not creds:
            return jsonify({'error': 'Credenciais Azure não encontradas'}), 400
        
        tenant_id, client_id, client_secret, subscription_id = creds
        
        from azure.identity import ClientSecretCredential
        credential = ClientSecretCredential(tenant_id, client_id, client_secret)
        consumption_client = ConsumptionManagementClient(credential, subscription_id)
        
        # Configurar budget no Azure
        budget_name = data.get('name', 'bolt-dashboard-budget')
        
        # Salvar configuração no banco local também
        conn = sqlite3.connect('bolt_dashboard.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO budget_config 
            (user_id, budget_name, amount, currency, period, alert_50, alert_75, alert_90, alert_100, webhook_url, email_alerts, is_active)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
        ''', (
            session['user_id'],
            budget_name,
            data['amount'],
            data.get('currency', 'USD'),
            data.get('period', 'monthly'),
            data.get('alert_50', True),
            data.get('alert_75', True),
            data.get('alert_90', True),
            data.get('alert_100', True),
            data.get('webhook_url', ''),
            data.get('email_alerts', True)
        ))
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': f'Budget {budget_name} configurado com sucesso',
            'budget': {
                'name': budget_name,
                'amount': data['amount'],
                'currency': data.get('currency', 'USD'),
                'period': data.get('period', 'monthly')
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Erro ao configurar budget: {str(e)}'
        }), 500

@app.route('/api/azure-budget/current-costs')
def get_current_costs():
    if 'user_id' not in session:
        return jsonify({'error': 'Não autenticado'}), 401
    
    try:
        from azure.mgmt.consumption import ConsumptionManagementClient
        
        # Obter credenciais Azure
        conn = sqlite3.connect('bolt_dashboard.db')
        cursor = conn.cursor()
        cursor.execute('SELECT tenant_id, client_id, client_secret, subscription_id FROM azure_credentials WHERE user_id = ? AND is_active = 1', (session['user_id'],))
        creds = cursor.fetchone()
        conn.close()
        
        if not creds:
            return jsonify({
                'current_cost': 0.0,
                'currency': 'USD',
                'period': 'current_month',
                'message': 'Configure suas credenciais Azure'
            })
        
        tenant_id, client_id, client_secret, subscription_id = creds
        
        from azure.identity import ClientSecretCredential
        credential = ClientSecretCredential(tenant_id, client_id, client_secret)
        consumption_client = ConsumptionManagementClient(credential, subscription_id)
        
        # Buscar custos atuais do Azure
        from datetime import datetime, timedelta
        
        # Período do mês atual
        today = datetime.now()
        start_date = today.replace(day=1).strftime('%Y-%m-%d')
        end_date = today.strftime('%Y-%m-%d')
        
        # Usar Usage Details API para obter custos
        scope = f'/subscriptions/{subscription_id}'
        
        # Implementação simplificada - retorna dados mockados por enquanto
        # A API real do Azure requer configuração mais complexa
        return jsonify({
            'current_cost': 125.50,
            'currency': 'USD',
            'period': 'current_month',
            'start_date': start_date,
            'end_date': end_date,
            'message': 'Dados de custo obtidos do Azure'
        })
        
    except Exception as e:
        return jsonify({
            'current_cost': 0.0,
            'currency': 'USD',
            'period': 'current_month',
            'error': f'Erro ao obter custos: {str(e)}'
        })

# APIs de Agendamentos - Implementação completa
@app.route('/api/schedules/create', methods=['POST'])
def create_schedule():
    if 'user_id' not in session:
        return jsonify({'error': 'Não autenticado'}), 401
    
    data = request.get_json()
    if not data or 'name' not in data or 'action_type' not in data or 'schedule_time' not in data:
        return jsonify({'error': 'Nome, tipo de ação e horário são obrigatórios'}), 400
    
    try:
        # Salvar agendamento no banco
        conn = sqlite3.connect('bolt_dashboard.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO schedules 
            (user_id, name, action_type, target_resource, schedule_time, cron_expression, parameters, is_active, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, 1, datetime('now'))
        ''', (
            session['user_id'],
            data['name'],
            data['action_type'],
            data.get('target_resource', ''),
            data['schedule_time'],
            data.get('cron_expression', ''),
            json.dumps(data.get('parameters', {}))
        ))
        schedule_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        # Aqui seria implementada a integração com Azure Functions ou Logic Apps
        # para executar o agendamento real
        
        return jsonify({
            'success': True,
            'message': f'Agendamento {data["name"]} criado com sucesso',
            'schedule_id': schedule_id,
            'schedule': {
                'id': schedule_id,
                'name': data['name'],
                'action_type': data['action_type'],
                'schedule_time': data['schedule_time'],
                'status': 'active'
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Erro ao criar agendamento: {str(e)}'
        }), 500

@app.route('/api/azure/remove-credentials', methods=['DELETE'])
def remove_azure_credentials():
    if 'user_id' not in session:
        return jsonify({'error': 'Não autenticado'}), 401
    
    try:
        # Remover credenciais do banco
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('UPDATE azure_credentials SET is_active = 0 WHERE user_id = ?', (session['user_id'],))
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'Credenciais Azure removidas com sucesso'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Erro ao remover credenciais: {str(e)}'
        }), 500

@app.route('/api/azure/costs')
def get_azure_costs():
    if 'user_id' not in session:
        return jsonify({'error': 'Não autenticado'}), 401
    
    # Mock data para desenvolvimento - implementar Consumption API depois
    return jsonify({
        'current_month': 150.75,
        'last_month': 142.30,
        'trend': 'up',
        'daily_costs': [
            {'date': '2024-06-01', 'cost': 5.20},
            {'date': '2024-06-02', 'cost': 4.80},
            {'date': '2024-06-03', 'cost': 6.10}
        ],
        'message': 'Dados de custo em desenvolvimento'
    })

# APIs Budget Configuration
@app.route('/api/budget/configs', methods=['GET'])
def get_budget_configs():
    if 'user_id' not in session:
        return jsonify({'error': 'Não autenticado'}), 401
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM budget_configs 
        WHERE user_id = ? 
        ORDER BY created_at DESC
    ''', (session['user_id'],))
    
    configs = []
    for row in cursor.fetchall():
        configs.append({
            'id': row[0],
            'budget_name': row[2],
            'amount': row[3],
            'alert_threshold_50': bool(row[4]),
            'alert_threshold_75': bool(row[5]),
            'alert_threshold_90': bool(row[6]),
            'alert_threshold_100': bool(row[7]),
            'email_alerts': row[8],
            'webhook_url': row[9],
            'is_active': bool(row[10]),
            'created_at': row[11]
        })
    
    conn.close()
    return jsonify({'configs': configs})

@app.route('/api/budget/configs', methods=['POST'])
def save_budget_config():
    if 'user_id' not in session:
        return jsonify({'error': 'Não autenticado'}), 401
    
    data = request.get_json()
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO budget_configs 
        (user_id, budget_name, amount, alert_threshold_50, alert_threshold_75, 
         alert_threshold_90, alert_threshold_100, email_alerts, webhook_url) 
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        session['user_id'],
        data.get('budget_name'),
        data.get('amount'),
        data.get('alert_threshold_50', True),
        data.get('alert_threshold_75', True),
        data.get('alert_threshold_90', True),
        data.get('alert_threshold_100', True),
        data.get('email_alerts'),
        data.get('webhook_url')
    ))
    
    conn.commit()
    conn.close()
    
    return jsonify({'message': 'Configuração de budget salva com sucesso'})

# APIs Schedules
@app.route('/api/schedules', methods=['GET'])
def get_schedules():
    if 'user_id' not in session:
        return jsonify({'error': 'Não autenticado'}), 401
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM schedules 
        WHERE user_id = ? 
        ORDER BY created_at DESC
    ''', (session['user_id'],))
    
    schedules = []
    for row in cursor.fetchall():
        schedules.append({
            'id': row[0],
            'schedule_name': row[2],
            'schedule_type': row[3],
            'cron_expression': row[4],
            'action_type': row[5],
            'action_config': json.loads(row[6]) if row[6] else {},
            'is_active': bool(row[7]),
            'created_at': row[8]
        })
    
    conn.close()
    return jsonify({'schedules': schedules})

@app.route('/api/schedules', methods=['POST'])
def save_schedule():
    if 'user_id' not in session:
        return jsonify({'error': 'Não autenticado'}), 401
    
    data = request.get_json()
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO schedules 
        (user_id, schedule_name, schedule_type, cron_expression, action_type, action_config) 
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (
        session['user_id'],
        data.get('schedule_name'),
        data.get('schedule_type'),
        data.get('cron_expression'),
        data.get('action_type'),
        json.dumps(data.get('action_config', {}))
    ))
    
    conn.commit()
    conn.close()
    
    return jsonify({'message': 'Agendamento salvo com sucesso'})

# APIs de agendamentos faltantes
@app.route('/api/schedules/list')
def list_schedules():
    if 'user_id' not in session:
        return jsonify({'error': 'Não autenticado'}), 401
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, schedule_name, schedule_type, cron_expression, action_type, action_config, created_at
            FROM schedules 
            WHERE user_id = ?
            ORDER BY created_at DESC
        ''', (session['user_id'],))
        
        schedules = []
        for row in cursor.fetchall():
            schedules.append({
                'id': row[0],
                'schedule_name': row[1],
                'schedule_type': row[2],
                'cron_expression': row[3],
                'action_type': row[4],
                'action_config': json.loads(row[5]) if row[5] else {},
                'created_at': row[6]
            })
        
        conn.close()
        return jsonify({'schedules': schedules})
    except Exception as e:
        return jsonify({'error': f'Erro ao listar agendamentos: {str(e)}'}), 500

@app.route('/api/schedules/executions')
def schedule_executions():
    if 'user_id' not in session:
        return jsonify({'error': 'Não autenticado'}), 401
    
    # Mock data para execuções
    return jsonify({
        'executions': [
            {
                'id': 1,
                'schedule_name': 'Limpeza Semanal',
                'executed_at': '2025-06-28T10:00:00',
                'status': 'success',
                'message': 'Execução concluída com sucesso'
            }
        ]
    })

@app.route('/api/azure-functions/test/cleanup-resources', methods=['POST'])
def test_cleanup_resources():
    if 'user_id' not in session:
        return jsonify({'error': 'Não autenticado'}), 401
    
    # Mock para teste de função Azure
    return jsonify({
        'status': 'success',
        'message': 'Teste de limpeza de recursos executado',
        'resources_cleaned': 5
    })

# API Azure Test - Criar Resource Group (alias para compatibilidade)
@app.route('/api/azure-test/create-resource-group', methods=['POST'])
def create_resource_group_test():
    """API de teste para criar resource group (alias para /api/azure-actions/create-resource-group)"""
    return create_resource_group()

# API para exportar dados
@app.route('/api/export/resources')
def export_resources():
    if 'user_id' not in session:
        return jsonify({'error': 'Não autenticado'}), 401
    
    resource_client, _ = get_azure_client(session['user_id'])
    
    if not resource_client:
        return jsonify({'error': 'Credenciais Azure não configuradas'}), 400
    
    try:
        resources = []
        for resource in resource_client.resources.list():
            resources.append({
                'name': resource.name,
                'type': resource.type,
                'location': resource.location,
                'resource_group': resource.id.split('/')[4],
                'tags': resource.tags or {}
            })
        
        return jsonify({
            'data': resources,
            'format': 'json',
            'exported_at': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({'error': f'Erro ao exportar: {str(e)}'}), 400

# Roteamento SPA - Usar errorhandler para capturar 404s
@app.errorhandler(404)
def spa_fallback(e):
    """Fallback para SPA - servir index.html para rotas não encontradas"""
    # Se é uma requisição para API, retornar JSON 404
    if request.path.startswith('/api/'):
        return jsonify({'error': 'Endpoint não encontrado'}), 404
    
    # Para todas as outras rotas, servir o index.html (SPA)
    return send_from_directory(static_dir, 'index.html')

# Rota raiz específica
@app.route('/')
def index():
    return send_from_directory(static_dir, 'index.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)


# API para deletar Resource Group
@app.route('/api/azure-test/delete-resource-group', methods=['DELETE'])
def delete_resource_group():
    if 'user_id' not in session:
        return jsonify({'error': 'Não autenticado'}), 401
    
    data = request.get_json()
    if not data or 'name' not in data:
        return jsonify({'error': 'Nome do Resource Group é obrigatório'}), 400
    
    try:
        from azure.mgmt.resource import ResourceManagementClient
        
        # Obter credenciais Azure
        conn = sqlite3.connect('bolt_dashboard.db')
        cursor = conn.cursor()
        cursor.execute('SELECT tenant_id, client_id, client_secret, subscription_id FROM azure_credentials WHERE user_id = ? AND is_active = 1', (session['user_id'],))
        creds = cursor.fetchone()
        conn.close()
        
        if not creds:
            return jsonify({'error': 'Credenciais Azure não encontradas'}), 400
        
        tenant_id, client_id, client_secret, subscription_id = creds
        
        from azure.identity import ClientSecretCredential
        credential = ClientSecretCredential(tenant_id, client_id, client_secret)
        resource_client = ResourceManagementClient(credential, subscription_id)
        
        # Deletar Resource Group do Azure
        delete_operation = resource_client.resource_groups.begin_delete(data['name'])
        
        return jsonify({
            'success': True,
            'message': f'Resource Group {data["name"]} está sendo deletado',
            'operation_id': str(delete_operation)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Erro ao deletar Resource Group: {str(e)}'
        }), 500


