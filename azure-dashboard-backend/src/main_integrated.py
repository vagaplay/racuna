import os
import sys
from flask import Flask, send_from_directory, jsonify, request, session
from flask_cors import CORS
import sqlite3
from datetime import datetime

# Configurar path
current_dir = os.path.dirname(os.path.abspath(__file__))
static_dir = os.path.join(os.path.dirname(current_dir), 'static')

# Criar app Flask
app = Flask(__name__, static_folder=static_dir, static_url_path='')

# Configurações de sessão
app.config['SECRET_KEY'] = 'bolt-dashboard-secret-key-2024'
app.config['SESSION_PERMANENT'] = False

# Configurar CORS
CORS(app, origins='*', supports_credentials=True)

# Banco de dados
DB_PATH = os.path.join(current_dir, 'bolt_dashboard.db')

def init_db():
    """Inicializar banco de dados"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            name TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_admin BOOLEAN DEFAULT FALSE
        )
    ''')
    
    cursor.execute('SELECT COUNT(*) FROM users WHERE email = ?', ('test@test.com',))
    if cursor.fetchone()[0] == 0:
        cursor.execute('''
            INSERT INTO users (email, password, name, is_admin) 
            VALUES (?, ?, ?, ?)
        ''', ('test@test.com', '123456', 'Usuário Teste', True))
    
    conn.commit()
    conn.close()

init_db()

# Servir frontend
@app.route('/')
def index():
    return send_from_directory(static_dir, 'index.html')

@app.route('/<path:path>')
def serve_file(path):
    try:
        return send_from_directory(static_dir, path)
    except:
        return send_from_directory(static_dir, 'index.html')

# APIs
@app.route('/api/health')
def health():
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})

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
        return jsonify({
            'message': 'Login realizado com sucesso',
            'user': {'id': user[0], 'email': user[1], 'name': user[3]}
        })
    else:
        return jsonify({'error': 'Credenciais inválidas'}), 401

@app.route('/api/auth/status')
def auth_status():
    if 'user_id' in session:
        return jsonify({
            'authenticated': True,
            'user': {'id': session['user_id'], 'email': session['user_email']}
        })
    else:
        return jsonify({'authenticated': False})

@app.route('/api/dashboard/overview')
def dashboard():
    if 'user_id' not in session:
        return jsonify({'error': 'Não autenticado'}), 401
    
    return jsonify({
        'total_resources': 0,
        'total_cost': 0.0,
        'active_alerts': 0,
        'resource_groups': 2
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

