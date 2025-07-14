"""
Rotas para configuração e gerenciamento de credenciais Azure
"""

from flask import Blueprint, request, jsonify, session
from src.services.azure_service import azure_auth_service, azure_resource_service
import logging

logger = logging.getLogger(__name__)

azure_config_bp = Blueprint('azure_config', __name__)

@azure_config_bp.route('/configure-credentials', methods=['POST'])
def configure_azure_credentials():
    """
    Configura credenciais de Service Principal para o usuário
    """
    try:
        # Verificação robusta de autenticação
        if 'user_id' not in session:
            return jsonify({
                'error': 'Usuário não autenticado',
                'session_debug': {
                    'has_session': bool(session),
                    'session_keys': list(session.keys()) if session else [],
                    'user_id_in_session': 'user_id' in session
                }
            }), 401
        
        user_id = session['user_id']
        
        # Verificar se usuário existe
        from src.models.user import User
        user = User.get_by_id(user_id)
        if not user:
            session.clear()
            return jsonify({'error': 'Usuário não encontrado'}), 401
        data = request.get_json()
        
        # Validar dados obrigatórios
        required_fields = ['tenant_id', 'client_id', 'client_secret', 'subscription_id']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'Campo obrigatório: {field}'}), 400
        
        # Configurar credenciais
        result = azure_auth_service.configure_service_principal(
            user_id=user_id,
            tenant_id=data['tenant_id'],
            client_id=data['client_id'],
            client_secret=data['client_secret'],
            subscription_id=data['subscription_id']
        )
        
        if result['success']:
            return jsonify({
                'success': True,
                'message': result['message'],
                'subscription_name': result['subscription_name'],
                'subscription_id': result['subscription_id']
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 400
            
    except Exception as e:
        logger.error(f"Erro ao configurar credenciais: {str(e)}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

@azure_config_bp.route('/credentials-status', methods=['GET'])
def get_credentials_status():
    """
    Verifica se usuário tem credenciais configuradas
    """
    try:
        # Verificação robusta de autenticação
        if 'user_id' not in session:
            return jsonify({
                'error': 'Usuário não autenticado',
                'session_debug': {
                    'has_session': bool(session),
                    'session_keys': list(session.keys()) if session else [],
                    'user_id_in_session': 'user_id' in session
                }
            }), 401
        
        user_id = session['user_id']
        
        # Verificar se usuário existe
        from src.models.user import User
        user = User.get_by_id(user_id)
        if not user:
            session.clear()
            return jsonify({'error': 'Usuário não encontrado'}), 401
        
        is_configured = azure_auth_service.is_user_authenticated(user_id)
        
        if is_configured:
            creds = azure_auth_service.get_user_credentials(user_id)
            return jsonify({
                'configured': True,
                'subscription_name': creds.subscription_name,
                'subscription_id': creds.subscription_id,
                'configured_at': creds.created_at.isoformat() if creds.created_at else None,
                'last_validated': creds.last_validated.isoformat() if creds.last_validated else None
            }), 200
        else:
            return jsonify({'configured': False}), 200
            
    except Exception as e:
        logger.error(f"Erro ao verificar status das credenciais: {str(e)}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

@azure_config_bp.route('/test-connection', methods=['POST'])
def test_azure_connection():
    """
    Testa conectividade com Azure usando credenciais configuradas
    """
    try:
        if 'user_id' not in session:
            return jsonify({'error': 'Usuário não autenticado'}), 401
        
        user_id = session['user_id']
        
        if not azure_auth_service.is_user_authenticated(user_id):
            return jsonify({'error': 'Credenciais Azure não configuradas'}), 400
        
        # Testar listagem de resource groups
        result = azure_resource_service.list_resource_groups(user_id)
        
        if 'error' in result:
            return jsonify({
                'success': False,
                'error': f'Erro ao conectar com Azure: {result["error"]}'
            }), 400
        
        return jsonify({
            'success': True,
            'message': 'Conexão testada com sucesso!',
            'resource_groups_count': result['count'],
            'resource_groups': result['resource_groups'][:5]  # Primeiros 5 para teste
        }), 200
        
    except Exception as e:
        logger.error(f"Erro ao testar conexão: {str(e)}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

@azure_config_bp.route('/remove-credentials', methods=['DELETE'])
def remove_azure_credentials():
    """
    Remove credenciais Azure do usuário
    """
    try:
        if 'user_id' not in session:
            return jsonify({'error': 'Usuário não autenticado'}), 401
        
        user_id = session['user_id']
        
        success = azure_auth_service.remove_user_credentials(user_id)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Credenciais removidas com sucesso'
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': 'Erro ao remover credenciais'
            }), 400
            
    except Exception as e:
        logger.error(f"Erro ao remover credenciais: {str(e)}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

@azure_config_bp.route('/test', methods=['GET'])
def test_endpoint():
    """Endpoint de teste simples"""
    if 'user_id' not in session:
        return jsonify({'error': 'Usuário não autenticado'}), 401
    
    return jsonify({
        'success': True,
        'message': 'Endpoint funcionando',
        'user_id': session['user_id']
    }), 200

