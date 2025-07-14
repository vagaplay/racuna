"""
Serviço simplificado para debug das credenciais Azure
"""

import logging
from typing import Optional, Dict, Any
from azure.identity import ClientSecretCredential
from azure.mgmt.subscription import SubscriptionClient
from azure.core.exceptions import ClientAuthenticationError, HttpResponseError

logger = logging.getLogger(__name__)

def test_azure_credentials(tenant_id: str, client_id: str, client_secret: str, subscription_id: str) -> Dict[str, Any]:
    """
    Testa credenciais Azure de forma simples
    """
    try:
        logger.info(f"Testando credenciais Azure...")
        logger.info(f"Tenant ID: {tenant_id}")
        logger.info(f"Client ID: {client_id}")
        logger.info(f"Subscription ID: {subscription_id}")
        
        # Criar credencial
        credential = ClientSecretCredential(
            tenant_id=tenant_id,
            client_id=client_id,
            client_secret=client_secret
        )
        
        logger.info("Credencial criada com sucesso")
        
        # Testar autenticação
        subscription_client = SubscriptionClient(credential)
        logger.info("Cliente de subscription criado")
        
        # Obter informações da subscription
        subscription = subscription_client.subscriptions.get(subscription_id)
        logger.info(f"Subscription obtida: {subscription.display_name}")
        
        return {
            'success': True,
            'message': 'Credenciais válidas',
            'subscription_name': subscription.display_name,
            'subscription_id': subscription.subscription_id,
            'tenant_id': tenant_id  # Usar o tenant_id passado como parâmetro
        }
        
    except ClientAuthenticationError as e:
        logger.error(f"Erro de autenticação: {str(e)}")
        return {
            'success': False,
            'error': 'Credenciais inválidas',
            'details': str(e)
        }
    except HttpResponseError as e:
        logger.error(f"Erro HTTP: {str(e)}")
        return {
            'success': False,
            'error': 'Erro ao acessar Azure',
            'details': str(e)
        }
    except Exception as e:
        logger.error(f"Erro inesperado: {str(e)}")
        return {
            'success': False,
            'error': 'Erro inesperado',
            'details': str(e)
        }

