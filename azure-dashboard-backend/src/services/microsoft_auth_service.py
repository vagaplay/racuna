"""
Serviço de autenticação Microsoft Entra ID (OAuth)
"""

import msal
import requests
import logging
from typing import Dict, Any, Optional
from flask import current_app, session, url_for
from src.models.user import User, db

logger = logging.getLogger(__name__)

class MicrosoftAuthService:
    """Serviço para autenticação OAuth com Microsoft Entra ID"""
    
    def __init__(self):
        # Configurações OAuth (em produção, usar variáveis de ambiente)
        self.client_id = "YOUR_CLIENT_ID"  # Será configurado
        self.client_secret = "YOUR_CLIENT_SECRET"  # Será configurado
        self.authority = "https://login.microsoftonline.com/common"
        self.scope = [
            "User.Read",
            "https://management.azure.com/user_impersonation"
        ]
        self.redirect_uri = None  # Será definido dinamicamente
    
    def configure_oauth(self, client_id: str, client_secret: str, redirect_uri: str):
        """Configura parâmetros OAuth"""
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
    
    def get_msal_app(self):
        """Cria instância do MSAL app"""
        return msal.ConfidentialClientApplication(
            client_id=self.client_id,
            client_credential=self.client_secret,
            authority=self.authority
        )
    
    def get_auth_url(self) -> str:
        """
        Gera URL de autorização para redirecionar usuário
        """
        try:
            msal_app = self.get_msal_app()
            
            # Gerar state para segurança
            import secrets
            state = secrets.token_urlsafe(32)
            session['oauth_state'] = state
            
            auth_url = msal_app.get_authorization_request_url(
                scopes=self.scope,
                state=state,
                redirect_uri=self.redirect_uri
            )
            
            return auth_url
            
        except Exception as e:
            logger.error(f"Erro ao gerar URL de autorização: {str(e)}")
            raise
    
    def handle_auth_callback(self, authorization_code: str, state: str) -> Dict[str, Any]:
        """
        Processa callback de autorização e obtém tokens
        """
        try:
            # Verificar state para segurança
            if state != session.get('oauth_state'):
                return {'error': 'State inválido - possível ataque CSRF'}
            
            msal_app = self.get_msal_app()
            
            # Trocar código por tokens
            result = msal_app.acquire_token_by_authorization_code(
                code=authorization_code,
                scopes=self.scope,
                redirect_uri=self.redirect_uri
            )
            
            if 'error' in result:
                logger.error(f"Erro OAuth: {result.get('error_description', result['error'])}")
                return {
                    'error': f"Erro de autenticação: {result.get('error_description', result['error'])}"
                }
            
            # Obter informações do usuário
            access_token = result['access_token']
            user_info = self.get_user_info(access_token)
            
            if 'error' in user_info:
                return user_info
            
            # Criar ou atualizar usuário no banco
            user = self.create_or_update_user(user_info, result)
            
            # Criar sessão
            session['user_id'] = user.id
            session['access_token'] = access_token
            session['refresh_token'] = result.get('refresh_token')
            
            # Limpar state
            session.pop('oauth_state', None)
            
            return {
                'success': True,
                'user': {
                    'id': user.id,
                    'email': user.email,
                    'name': user.name
                },
                'message': 'Login realizado com sucesso'
            }
            
        except Exception as e:
            logger.error(f"Erro no callback OAuth: {str(e)}")
            return {'error': f'Erro interno: {str(e)}'}
    
    def get_user_info(self, access_token: str) -> Dict[str, Any]:
        """
        Obtém informações do usuário usando access token
        """
        try:
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            
            response = requests.get(
                'https://graph.microsoft.com/v1.0/me',
                headers=headers
            )
            
            if response.status_code != 200:
                return {'error': f'Erro ao obter dados do usuário: {response.status_code}'}
            
            user_data = response.json()
            
            return {
                'id': user_data.get('id'),
                'email': user_data.get('mail') or user_data.get('userPrincipalName'),
                'name': user_data.get('displayName'),
                'given_name': user_data.get('givenName'),
                'surname': user_data.get('surname')
            }
            
        except Exception as e:
            logger.error(f"Erro ao obter informações do usuário: {str(e)}")
            return {'error': f'Erro ao obter dados do usuário: {str(e)}'}
    
    def create_or_update_user(self, user_info: Dict[str, Any], token_result: Dict[str, Any]) -> User:
        """
        Cria ou atualiza usuário no banco de dados
        """
        try:
            # Buscar usuário existente por Entra ID ou email
            user = User.query.filter_by(entra_id=user_info['id']).first()
            
            if not user:
                user = User.query.filter_by(email=user_info['email']).first()
            
            if user:
                # Atualizar usuário existente
                user.entra_id = user_info['id']
                user.email = user_info['email']
                user.name = user_info['name']
            else:
                # Criar novo usuário
                user = User(
                    entra_id=user_info['id'],
                    email=user_info['email'],
                    name=user_info['name']
                )
                db.session.add(user)
            
            db.session.commit()
            return user
            
        except Exception as e:
            logger.error(f"Erro ao criar/atualizar usuário: {str(e)}")
            db.session.rollback()
            raise
    
    def refresh_access_token(self, user_id: int) -> Optional[str]:
        """
        Renova access token usando refresh token
        """
        try:
            refresh_token = session.get('refresh_token')
            if not refresh_token:
                return None
            
            msal_app = self.get_msal_app()
            
            result = msal_app.acquire_token_by_refresh_token(
                refresh_token=refresh_token,
                scopes=self.scope
            )
            
            if 'error' in result:
                logger.error(f"Erro ao renovar token: {result.get('error_description')}")
                return None
            
            # Atualizar tokens na sessão
            session['access_token'] = result['access_token']
            if 'refresh_token' in result:
                session['refresh_token'] = result['refresh_token']
            
            return result['access_token']
            
        except Exception as e:
            logger.error(f"Erro ao renovar access token: {str(e)}")
            return None
    
    def get_azure_credentials_from_token(self, user_id: int) -> Optional[Dict[str, str]]:
        """
        Obtém credenciais Azure usando token do usuário
        """
        try:
            access_token = session.get('access_token')
            if not access_token:
                # Tentar renovar token
                access_token = self.refresh_access_token(user_id)
                if not access_token:
                    return None
            
            # Com o token do usuário, podemos acessar recursos Azure
            # usando delegated permissions
            return {
                'access_token': access_token,
                'token_type': 'Bearer'
            }
            
        except Exception as e:
            logger.error(f"Erro ao obter credenciais Azure: {str(e)}")
            return None
    
    def logout_user(self):
        """
        Faz logout do usuário
        """
        try:
            # Limpar sessão
            session.pop('user_id', None)
            session.pop('access_token', None)
            session.pop('refresh_token', None)
            session.pop('oauth_state', None)
            
            # URL de logout do Microsoft
            logout_url = f"{self.authority}/oauth2/v2.0/logout"
            
            return {
                'success': True,
                'logout_url': logout_url
            }
            
        except Exception as e:
            logger.error(f"Erro no logout: {str(e)}")
            return {'error': f'Erro no logout: {str(e)}'}

# Instância global do serviço
microsoft_auth_service = MicrosoftAuthService()

