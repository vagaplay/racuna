import os
import sys
from flask import Flask, send_from_directory, send_file, jsonify, request, session
from flask_cors import CORS
import sqlite3
from datetime import datetime
import json

app = Flask(__name__, static_folder='static')
app.config['SECRET_KEY'] = 'your_super_secret_key_here'

# Configurações de sessão
app.config['SESSION_COOKIE_SECURE'] = False
app.config['SESSION_COOKIE_HTTPONLY'] = False
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_DOMAIN'] = None
app.config['SESSION_COOKIE_PATH'] = '/'
app.config['PERMANENT_SESSION_LIFETIME'] = 7200
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_PERMANENT'] = True

# CORS configuração
CORS(app, 
     origins=['*'],
     supports_credentials=True,
     allow_headers=['Content-Type', 'Authorization', 'Cookie'],
     methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'])

# Banco de dados simples
DB_PATH = 'bolt_dashboard.db'

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
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Inserir usuário de teste se não existir
    cursor.execute('SELECT COUNT(*) FROM users WHERE email = ?', ('test@test.com',))
    if cursor.fetchone()[0] == 0:
        cursor.execute(
            'INSERT INTO users (email, password, name) VALUES (?, ?, ?)',
            ('test@test.com', '123456', 'Usuário Teste')
        )
    
    conn.commit()
    conn.close()

# Rotas da API
@app.route('/api/auth/login', methods=['POST'])
def login():
    """Login do usuário"""
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('SELECT id, email, name FROM users WHERE email = ? AND password = ?', (email, password))
        user = cursor.fetchone()
        conn.close()
        
        if user:
            session['user_id'] = user[0]
            session['user_email'] = user[1]
            session.permanent = True
            
            return jsonify({
                'message': 'Login successful',
                'user': {
                    'id': user[0],
                    'email': user[1],
                    'name': user[2]
                }
            })
        else:
            return jsonify({'error': 'Credenciais inválidas'}), 401
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/auth/status', methods=['GET'])
def auth_status():
    """Verificar status de autenticação"""
    if 'user_id' in session:
        return jsonify({
            'authenticated': True,
            'user': {
                'id': session['user_id'],
                'email': session['user_email']
            }
        })
    else:
        return jsonify({'authenticated': False}), 401

@app.route('/api/auth/logout', methods=['POST'])
def logout():
    """Logout do usuário"""
    session.clear()
    return jsonify({'message': 'Logout successful'})

@app.route('/api/health', methods=['GET'])
def health():
    """Health check"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0'
    })

@app.route('/api/azure-budget/current-costs', methods=['GET'])
def current_costs():
    """Custos atuais (dados fictícios para demo)"""
    return jsonify({
        'current_month': {
            'total': 0.00,
            'currency': 'BRL',
            'period': 'Dezembro 2024'
        },
        'last_month': {
            'total': 0.00,
            'currency': 'BRL',
            'period': 'Novembro 2024'
        },
        'trend': 'stable',
        'daily_costs': []
    })

@app.route('/api/monitoring/dashboard', methods=['GET'])
def monitoring_dashboard():
    """Dashboard de monitoramento"""
    return jsonify({
        'resources': {
            'total': 2,
            'running': 0,
            'stopped': 2
        },
        'alerts': {
            'critical': 0,
            'warning': 0,
            'info': 1
        },
        'costs': {
            'current_month': 0.00,
            'last_month': 0.00,
            'currency': 'BRL'
        }
    })

# Servir frontend
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    static_folder_path = app.static_folder
    if static_folder_path is None:
        return "Static folder not configured", 404

    if path != "" and os.path.exists(os.path.join(static_folder_path, path)):
        return send_from_directory(static_folder_path, path)
    else:
        index_path = os.path.join(static_folder_path, 'index.html')
        if os.path.exists(index_path):
            return send_from_directory(static_folder_path, 'index.html')
        else:
            return "index.html not found", 404

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000, debug=True)

