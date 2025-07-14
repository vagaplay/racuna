"""
Rota de debug para testar credenciais Azure
"""

from flask import Blueprint, request, jsonify, session
from src.services.azure_debug import test_azure_credentials
import logging

logger = logging.getLogger(__name__)

azure_debug_bp = Blueprint('azure_debug', __name__)

@azure_debug_bp.route('/test-credentials', methods=['POST'])
def debug_azure_credentials():
    """
    Testa credenciais Azure de forma simplificada para debug
    """
    try:
        # Verificar se usuário está logado
        if 'user_id' not in session:
            return jsonify({'error': 'Usuário não autenticado'}), 401
        
        data = request.get_json()
        
        # Validar dados obrigatórios
        required_fields = ['tenant_id', 'client_id', 'client_secret', 'subscription_id']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'Campo obrigatório: {field}'}), 400
        
        logger.info("Iniciando teste de credenciais Azure...")
        
        # Testar credenciais
        result = test_azure_credentials(
            tenant_id=data['tenant_id'],
            client_id=data['client_id'],
            client_secret=data['client_secret'],
            subscription_id=data['subscription_id']
        )
        
        logger.info(f"Resultado do teste: {result}")
        
        if result['success']:
            return jsonify({
                'success': True,
                'message': 'Credenciais testadas com sucesso!',
                'subscription_name': result['subscription_name'],
                'subscription_id': result['subscription_id'],
                'tenant_id': result.get('tenant_id'),
                'debug': True
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': result['error'],
                'details': result.get('details'),
                'debug': True
            }), 400
        
    except Exception as e:
        logger.error(f"Erro no debug de credenciais: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Erro interno no debug',
            'details': str(e),
            'debug': True
        }), 500

