"""
Rotas para autenticação Microsoft Entra ID
"""

from flask import Blueprint, request, jsonify, session, redirect, url_for
from src.services.microsoft_auth_service import microsoft_auth_service
import logging

logger = logging.getLogger(__name__)

microsoft_auth_bp = Blueprint('microsoft_auth', __name__)

@microsoft_auth_bp.route('/config', methods=['POST'])
def configure_microsoft_oauth():
    """
    Configura parâmetros OAuth do Microsoft Entra ID
    """
    try:
        data = request.get_json()
        
        required_fields = ['client_id', 'client_secret', 'redirect_uri']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'Campo obrigatório: {field}'}), 400
        
        microsoft_auth_service.configure_oauth(
            client_id=data['client_id'],
            client_secret=data['client_secret'],
            redirect_uri=data['redirect_uri']
        )
        
        return jsonify({
            'success': True,
            'message': 'Configuração OAuth atualizada com sucesso'
        }), 200
        
    except Exception as e:
        logger.error(f"Erro ao configurar OAuth: {str(e)}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

@microsoft_auth_bp.route('/login', methods=['GET'])
def microsoft_login():
    """
    Inicia processo de login com Microsoft
    """
    try:
        # Configurar redirect URI dinamicamente
        redirect_uri = request.args.get('redirect_uri') or f"{request.host_url}api/microsoft/callback"
        
        # Configuração padrão para desenvolvimento
        microsoft_auth_service.configure_oauth(
            client_id="YOUR_CLIENT_ID",  # Será configurado pelo usuário
            client_secret="YOUR_CLIENT_SECRET",  # Será configurado pelo usuário
            redirect_uri=redirect_uri
        )
        
        auth_url = microsoft_auth_service.get_auth_url()
        
        return jsonify({
            'success': True,
            'auth_url': auth_url,
            'message': 'Redirecionando para Microsoft...'
        }), 200
        
    except Exception as e:
        logger.error(f"Erro ao iniciar login Microsoft: {str(e)}")
        return jsonify({'error': 'Erro ao iniciar autenticação'}), 500

@microsoft_auth_bp.route('/callback', methods=['GET'])
def microsoft_callback():
    """
    Processa callback de autorização do Microsoft
    """
    try:
        # Obter parâmetros do callback
        authorization_code = request.args.get('code')
        state = request.args.get('state')
        error = request.args.get('error')
        
        if error:
            error_description = request.args.get('error_description', error)
            logger.error(f"Erro OAuth: {error_description}")
            return redirect(f"/login?error={error_description}")
        
        if not authorization_code:
            return redirect("/login?error=Código de autorização não recebido")
        
        # Processar callback
        result = microsoft_auth_service.handle_auth_callback(authorization_code, state)
        
        if 'error' in result:
            return redirect(f"/login?error={result['error']}")
        
        # Sucesso - redirecionar para dashboard
        return redirect("/dashboard?login=success")
        
    except Exception as e:
        logger.error(f"Erro no callback Microsoft: {str(e)}")
        return redirect(f"/login?error=Erro interno no callback")

@microsoft_auth_bp.route('/logout', methods=['POST'])
def microsoft_logout():
    """
    Faz logout do usuário Microsoft
    """
    try:
        result = microsoft_auth_service.logout_user()
        
        if 'error' in result:
            return jsonify(result), 400
        
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"Erro no logout Microsoft: {str(e)}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

@microsoft_auth_bp.route('/status', methods=['GET'])
def microsoft_auth_status():
    """
    Verifica status da autenticação Microsoft
    """
    try:
        user_id = session.get('user_id')
        access_token = session.get('access_token')
        
        if user_id and access_token:
            return jsonify({
                'authenticated': True,
                'user_id': user_id,
                'has_token': True
            }), 200
        else:
            return jsonify({
                'authenticated': False,
                'has_token': False
            }), 200
            
    except Exception as e:
        logger.error(f"Erro ao verificar status: {str(e)}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

@microsoft_auth_bp.route('/user-info', methods=['GET'])
def get_microsoft_user_info():
    """
    Obtém informações do usuário autenticado
    """
    try:
        if 'user_id' not in session:
            return jsonify({'error': 'Usuário não autenticado'}), 401
        
        access_token = session.get('access_token')
        if not access_token:
            return jsonify({'error': 'Token de acesso não encontrado'}), 401
        
        user_info = microsoft_auth_service.get_user_info(access_token)
        
        if 'error' in user_info:
            return jsonify(user_info), 400
        
        return jsonify({
            'success': True,
            'user': user_info
        }), 200
        
    except Exception as e:
        logger.error(f"Erro ao obter informações do usuário: {str(e)}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

@microsoft_auth_bp.route('/test', methods=['GET'])
def test_microsoft_auth():
    """
    Endpoint de teste para autenticação Microsoft
    """
    return jsonify({
        'success': True,
        'message': 'Serviço de autenticação Microsoft funcionando',
        'authenticated': 'user_id' in session,
        'session_keys': list(session.keys())
    }), 200

