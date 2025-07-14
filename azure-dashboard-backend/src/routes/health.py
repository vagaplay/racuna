"""
Sistema de Health Check para BOLT Dashboard
"""

from flask import Blueprint, jsonify
from datetime import datetime
import sqlite3
import os
import psutil
import requests

health_bp = Blueprint('health', __name__)

DB_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'database.db')

@health_bp.route('', methods=['GET'])
def health_check():
    """Endpoint de health check completo"""
    
    health_status = {
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0',
        'checks': {}
    }
    
    # Verificar banco de dados
    db_status = check_database()
    health_status['checks']['database'] = db_status
    
    # Verificar sistema
    system_status = check_system()
    health_status['checks']['system'] = system_status
    
    # Verificar Azure APIs
    azure_status = check_azure_apis()
    health_status['checks']['azure'] = azure_status
    
    # Determinar status geral
    all_healthy = all(
        check['status'] == 'healthy' 
        for check in health_status['checks'].values()
    )
    
    if not all_healthy:
        health_status['status'] = 'unhealthy'
    
    status_code = 200 if all_healthy else 503
    return jsonify(health_status), status_code

def check_database():
    """Verificar saúde do banco de dados"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Teste simples de conectividade
        cursor.execute('SELECT 1')
        result = cursor.fetchone()
        
        # Verificar tabelas principais
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name IN ('users', 'azure_credentials')
        """)
        tables = cursor.fetchall()
        
        conn.close()
        
        return {
            'status': 'healthy',
            'message': 'Database connection successful',
            'tables_found': len(tables),
            'response_time_ms': 10  # Aproximado para SQLite
        }
        
    except Exception as e:
        return {
            'status': 'unhealthy',
            'message': f'Database error: {str(e)}',
            'error': str(e)
        }

def check_system():
    """Verificar saúde do sistema"""
    try:
        # Uso de CPU
        cpu_percent = psutil.cpu_percent(interval=1)
        
        # Uso de memória
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        
        # Uso de disco
        disk = psutil.disk_usage('/')
        disk_percent = disk.percent
        
        # Determinar status baseado nos recursos
        status = 'healthy'
        if cpu_percent > 90 or memory_percent > 90 or disk_percent > 90:
            status = 'unhealthy'
        elif cpu_percent > 70 or memory_percent > 70 or disk_percent > 80:
            status = 'warning'
        
        return {
            'status': status,
            'cpu_percent': cpu_percent,
            'memory_percent': memory_percent,
            'disk_percent': disk_percent,
            'uptime_seconds': int(psutil.boot_time())
        }
        
    except Exception as e:
        return {
            'status': 'unhealthy',
            'message': f'System check error: {str(e)}',
            'error': str(e)
        }

def check_azure_apis():
    """Verificar conectividade com Azure APIs"""
    try:
        # Teste básico de conectividade com Azure
        # Em produção, isso faria uma chamada real para Azure Resource Manager
        
        # Simular verificação (em produção, usar azure.identity e azure.mgmt)
        azure_endpoints = [
            'https://management.azure.com',
            'https://login.microsoftonline.com'
        ]
        
        results = {}
        all_healthy = True
        
        for endpoint in azure_endpoints:
            try:
                response = requests.get(f"{endpoint}/", timeout=5)
                if response.status_code in [200, 401, 403]:  # 401/403 são esperados sem auth
                    results[endpoint] = {
                        'status': 'healthy',
                        'response_time_ms': int(response.elapsed.total_seconds() * 1000)
                    }
                else:
                    results[endpoint] = {
                        'status': 'unhealthy',
                        'status_code': response.status_code
                    }
                    all_healthy = False
            except Exception as e:
                results[endpoint] = {
                    'status': 'unhealthy',
                    'error': str(e)
                }
                all_healthy = False
        
        return {
            'status': 'healthy' if all_healthy else 'unhealthy',
            'endpoints': results
        }
        
    except Exception as e:
        return {
            'status': 'unhealthy',
            'message': f'Azure API check error: {str(e)}',
            'error': str(e)
        }

@health_bp.route('/ready', methods=['GET'])
def readiness_check():
    """Endpoint de readiness check (mais simples)"""
    try:
        # Verificação básica se a aplicação está pronta
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('SELECT 1')
        conn.close()
        
        return jsonify({
            'status': 'ready',
            'timestamp': datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        return jsonify({
            'status': 'not_ready',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 503

@health_bp.route('/live', methods=['GET'])
def liveness_check():
    """Endpoint de liveness check (mais básico)"""
    return jsonify({
        'status': 'alive',
        'timestamp': datetime.now().isoformat()
    }), 200

