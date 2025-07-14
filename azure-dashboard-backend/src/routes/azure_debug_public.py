"""
Rota de debug público para testar credenciais Azure (sem autenticação)
"""

from flask import Blueprint, request, jsonify
from src.services.azure_debug import test_azure_credentials
import logging

logger = logging.getLogger(__name__)

azure_debug_public_bp = Blueprint('azure_debug_public', __name__)

@azure_debug_public_bp.route('/test-credentials-public', methods=['POST'])
def debug_azure_credentials_public():
    """
    Testa credenciais Azure de forma simplificada para debug (SEM AUTENTICAÇÃO)
    """
    try:
        data = request.get_json()
        
        # Validar dados obrigatórios
        required_fields = ['tenant_id', 'client_id', 'client_secret', 'subscription_id']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'Campo obrigatório: {field}'}), 400
        
        logger.info("Iniciando teste PÚBLICO de credenciais Azure...")
        
        # Testar credenciais
        result = test_azure_credentials(
            tenant_id=data['tenant_id'],
            client_id=data['client_id'],
            client_secret=data['client_secret'],
            subscription_id=data['subscription_id']
        )
        
        logger.info(f"Resultado do teste público: {result}")
        
        if result['success']:
            return jsonify({
                'success': True,
                'message': 'Credenciais testadas com sucesso!',
                'subscription_name': result['subscription_name'],
                'subscription_id': result['subscription_id'],
                'tenant_id': result.get('tenant_id'),
                'debug': True,
                'public_test': True
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': result['error'],
                'details': result.get('details'),
                'debug': True,
                'public_test': True
            }), 400
        
    except Exception as e:
        logger.error(f"Erro no debug público de credenciais: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Erro interno no debug',
            'details': str(e),
            'debug': True,
            'public_test': True
        }), 500

@azure_debug_public_bp.route('/health', methods=['GET'])
def health_check_public():
    """Health check público"""
    return jsonify({
        'status': 'healthy',
        'message': 'Azure Debug Public API is running',
        'public': True
    })

