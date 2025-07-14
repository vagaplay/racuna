"""
Endpoint para verificar status de autenticação
"""

from flask import Blueprint, jsonify, session
from src.models.user import User

auth_status_bp = Blueprint('auth_status', __name__)

@auth_status_bp.route('/status', methods=['GET'])
def auth_status():
    """Verificar se o usuário está autenticado"""
    try:
        if 'user_id' in session:
            user_id = session['user_id']
            user = User.get_by_id(user_id)
            
            if user:
                return jsonify({
                    'authenticated': True,
                    'user': {
                        'id': user.id,
                        'email': user.email,
                        'name': user.name
                    },
                    'session_id': session.get('_id', 'no_session_id')
                }), 200
            else:
                # Usuário não existe mais, limpar sessão
                session.clear()
                return jsonify({
                    'authenticated': False,
                    'message': 'Usuário não encontrado'
                }), 401
        else:
            return jsonify({
                'authenticated': False,
                'message': 'Não autenticado'
            }), 401
            
    except Exception as e:
        return jsonify({
            'authenticated': False,
            'error': str(e)
        }), 500

