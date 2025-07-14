"""
Sistema de Agendamentos Avançados
"""

from flask import Blueprint, request, jsonify, session
from datetime import datetime, timedelta
import json
import sqlite3
import os

schedules_bp = Blueprint('schedules', __name__)

DB_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'database.db')

def init_schedules_db():
    """Inicializar tabela de agendamentos"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS schedules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            type TEXT NOT NULL,
            schedule_type TEXT NOT NULL,
            time TEXT NOT NULL,
            days_of_week TEXT,
            target_scope TEXT NOT NULL,
            target_value TEXT NOT NULL,
            enabled BOOLEAN DEFAULT 1,
            notification_email TEXT,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_run TIMESTAMP,
            next_run TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS schedule_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            schedule_id INTEGER NOT NULL,
            execution_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status TEXT NOT NULL,
            message TEXT,
            resources_affected INTEGER DEFAULT 0,
            FOREIGN KEY (schedule_id) REFERENCES schedules (id)
        )
    ''')
    
    conn.commit()
    conn.close()

@schedules_bp.route('', methods=['GET'])
def list_schedules():
    """Listar agendamentos do usuário"""
    if 'user_id' not in session:
        return jsonify({'error': 'Usuário não autenticado'}), 401
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, name, type, schedule_type, time, days_of_week, 
                   target_scope, target_value, enabled, notification_email, 
                   description, created_at, last_run, next_run
            FROM schedules 
            WHERE user_id = ? 
            ORDER BY created_at DESC
        ''', (session['user_id'],))
        
        schedules = []
        for row in cursor.fetchall():
            schedule = {
                'id': row[0],
                'name': row[1],
                'type': row[2],
                'schedule_type': row[3],
                'time': row[4],
                'days_of_week': json.loads(row[5]) if row[5] else [],
                'target_scope': row[6],
                'target_value': row[7],
                'enabled': bool(row[8]),
                'notification_email': row[9],
                'description': row[10],
                'created_at': row[11],
                'last_run': row[12],
                'next_run': row[13]
            }
            schedules.append(schedule)
        
        conn.close()
        return jsonify({'schedules': schedules}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@schedules_bp.route('', methods=['POST'])
def create_schedule():
    """Criar novo agendamento"""
    if 'user_id' not in session:
        return jsonify({'error': 'Usuário não autenticado'}), 401
    
    try:
        data = request.get_json()
        
        # Validações
        required_fields = ['name', 'type', 'schedule_type', 'time', 'target_scope', 'target_value']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'Campo {field} é obrigatório'}), 400
        
        # Calcular próxima execução
        next_run = calculate_next_run(data['schedule_type'], data['time'], data.get('days_of_week', []))
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO schedules (
                user_id, name, type, schedule_type, time, days_of_week,
                target_scope, target_value, enabled, notification_email,
                description, next_run
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            session['user_id'],
            data['name'],
            data['type'],
            data['schedule_type'],
            data['time'],
            json.dumps(data.get('days_of_week', [])),
            data['target_scope'],
            data['target_value'],
            data.get('enabled', True),
            data.get('notification_email'),
            data.get('description'),
            next_run
        ))
        
        schedule_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return jsonify({
            'message': 'Agendamento criado com sucesso',
            'schedule_id': schedule_id
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@schedules_bp.route('/<int:schedule_id>/toggle', methods=['POST'])
def toggle_schedule(schedule_id):
    """Ativar/desativar agendamento"""
    if 'user_id' not in session:
        return jsonify({'error': 'Usuário não autenticado'}), 401
    
    try:
        data = request.get_json()
        enabled = data.get('enabled', True)
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Verificar se o agendamento pertence ao usuário
        cursor.execute(
            'SELECT id FROM schedules WHERE id = ? AND user_id = ?',
            (schedule_id, session['user_id'])
        )
        
        if not cursor.fetchone():
            return jsonify({'error': 'Agendamento não encontrado'}), 404
        
        cursor.execute(
            'UPDATE schedules SET enabled = ? WHERE id = ?',
            (enabled, schedule_id)
        )
        
        conn.commit()
        conn.close()
        
        return jsonify({'message': 'Status do agendamento atualizado'}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@schedules_bp.route('/<int:schedule_id>', methods=['DELETE'])
def delete_schedule(schedule_id):
    """Excluir agendamento"""
    if 'user_id' not in session:
        return jsonify({'error': 'Usuário não autenticado'}), 401
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Verificar se o agendamento pertence ao usuário
        cursor.execute(
            'SELECT id FROM schedules WHERE id = ? AND user_id = ?',
            (schedule_id, session['user_id'])
        )
        
        if not cursor.fetchone():
            return jsonify({'error': 'Agendamento não encontrado'}), 404
        
        # Excluir logs relacionados
        cursor.execute('DELETE FROM schedule_logs WHERE schedule_id = ?', (schedule_id,))
        
        # Excluir agendamento
        cursor.execute('DELETE FROM schedules WHERE id = ?', (schedule_id,))
        
        conn.commit()
        conn.close()
        
        return jsonify({'message': 'Agendamento excluído com sucesso'}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@schedules_bp.route('/<int:schedule_id>/logs', methods=['GET'])
def get_schedule_logs(schedule_id):
    """Obter logs de execução do agendamento"""
    if 'user_id' not in session:
        return jsonify({'error': 'Usuário não autenticado'}), 401
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Verificar se o agendamento pertence ao usuário
        cursor.execute(
            'SELECT id FROM schedules WHERE id = ? AND user_id = ?',
            (schedule_id, session['user_id'])
        )
        
        if not cursor.fetchone():
            return jsonify({'error': 'Agendamento não encontrado'}), 404
        
        cursor.execute('''
            SELECT execution_time, status, message, resources_affected
            FROM schedule_logs 
            WHERE schedule_id = ? 
            ORDER BY execution_time DESC 
            LIMIT 50
        ''', (schedule_id,))
        
        logs = []
        for row in cursor.fetchall():
            logs.append({
                'execution_time': row[0],
                'status': row[1],
                'message': row[2],
                'resources_affected': row[3]
            })
        
        conn.close()
        return jsonify({'logs': logs}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def calculate_next_run(schedule_type, time, days_of_week):
    """Calcular próxima execução do agendamento"""
    from datetime import datetime, timedelta
    
    now = datetime.now()
    time_parts = time.split(':')
    hour = int(time_parts[0])
    minute = int(time_parts[1])
    
    if schedule_type == 'daily':
        # Próxima execução hoje se ainda não passou, senão amanhã
        next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if next_run <= now:
            next_run += timedelta(days=1)
    
    elif schedule_type == 'weekly':
        # Encontrar próximo dia da semana especificado
        weekdays = {
            'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3,
            'friday': 4, 'saturday': 5, 'sunday': 6
        }
        
        target_weekdays = [weekdays[day] for day in days_of_week if day in weekdays]
        if not target_weekdays:
            target_weekdays = [0]  # Default para segunda-feira
        
        current_weekday = now.weekday()
        days_ahead = min([
            (day - current_weekday) % 7 for day in target_weekdays
            if (day - current_weekday) % 7 > 0 or 
               (day == current_weekday and now.time() < datetime.strptime(time, '%H:%M').time())
        ] + [7])  # Se nenhum dia válido hoje, próxima semana
        
        next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        next_run += timedelta(days=days_ahead)
    
    return next_run.isoformat()

# Inicializar banco ao importar
init_schedules_db()

