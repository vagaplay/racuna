"""
Serviço de autenticação e integração com Azure
Gerencia credenciais de Service Principal e autenticação com APIs Azure
"""

import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from azure.identity import ClientSecretCredential
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.costmanagement import CostManagementClient
from azure.mgmt.consumption import ConsumptionManagementClient
from azure.mgmt.subscription import SubscriptionClient
from azure.core.exceptions import ClientAuthenticationError, HttpResponseError
from src.models.azure_credentials import AzureCredentials, db

logger = logging.getLogger(__name__)

class AzureAuthService:
    """Serviço para autenticação e operações Azure"""
    
    def __init__(self):
        self.active_clients = {}  # Cache de clientes ativos
    
    def configure_service_principal(self, user_id: int, tenant_id: str, 
                                  client_id: str, client_secret: str, 
                                  subscription_id: str) -> Dict[str, Any]:
        """
        Configura credenciais de Service Principal para um usuário
        """
        try:
            # Criar credencial para teste
            credential = ClientSecretCredential(
                tenant_id=tenant_id,
                client_id=client_id,
                client_secret=client_secret
            )
            
            # Testar autenticação obtendo informações da subscription
            subscription_client = SubscriptionClient(credential)
            subscription = subscription_client.subscriptions.get(subscription_id)
            
            # Se chegou até aqui, as credenciais são válidas
            # Verificar se já existem credenciais para este usuário
            existing_creds = AzureCredentials.get_by_user_id(user_id)
            
            if existing_creds:
                # Atualizar credenciais existentes
                existing_creds.update_credentials(
                    tenant_id=tenant_id,
                    client_id=client_id,
                    client_secret=client_secret,
                    subscription_id=subscription_id,
                    subscription_name=subscription.display_name
                )
                existing_creds.mark_as_validated()
            else:
                # Criar novas credenciais
                new_creds = AzureCredentials(
                    user_id=user_id,
                    tenant_id=tenant_id,
                    client_id=client_id,
                    client_secret=client_secret,
                    subscription_id=subscription_id,
                    subscription_name=subscription.display_name
                )
                new_creds.mark_as_validated()
                db.session.add(new_creds)
            
            db.session.commit()
            
            # Limpar cache de clientes para este usuário
            if user_id in self.active_clients:
                del self.active_clients[user_id]
            
            logger.info(f"Service Principal configurado com sucesso para usuário {user_id}")
            
            return {
                'success': True,
                'subscription_name': subscription.display_name,
                'subscription_id': subscription_id,
                'message': 'Credenciais configuradas com sucesso'
            }
            
        except ClientAuthenticationError as e:
            logger.error(f"Erro de autenticação: {str(e)}")
            return {
                'success': False,
                'error': 'Credenciais inválidas. Verifique Tenant ID, Client ID e Client Secret.',
                'details': str(e)
            }
        except Exception as e:
            logger.error(f"Erro ao configurar Service Principal: {str(e)}")
            return {
                'success': False,
                'error': 'Erro interno ao configurar credenciais',
                'details': str(e)
            }
    
    def get_user_credentials(self, user_id: int) -> Optional[AzureCredentials]:
        """Obtém credenciais configuradas para um usuário"""
        return AzureCredentials.get_by_user_id(user_id)
    
    def is_user_authenticated(self, user_id: int) -> bool:
        """Verifica se usuário tem credenciais válidas configuradas"""
        creds = self.get_user_credentials(user_id)
        return creds is not None and creds.is_active
    
    def get_credential_object(self, user_id: int) -> Optional[ClientSecretCredential]:
        """Obtém objeto de credencial Azure para um usuário"""
        creds = self.get_user_credentials(user_id)
        if not creds:
            return None
        
        return ClientSecretCredential(
            tenant_id=creds.tenant_id,
            client_id=creds.client_id,
            client_secret=creds.get_client_secret()
        )
    
    def get_resource_client(self, user_id: int) -> Optional[ResourceManagementClient]:
        """Obtém cliente de Resource Management para um usuário"""
        if not self.is_user_authenticated(user_id):
            return None
        
        if user_id not in self.active_clients:
            self.active_clients[user_id] = {}
        
        if 'resource' not in self.active_clients[user_id]:
            creds = self.get_user_credentials(user_id)
            credential = self.get_credential_object(user_id)
            
            self.active_clients[user_id]['resource'] = ResourceManagementClient(
                credential,
                creds.subscription_id
            )
        
        return self.active_clients[user_id]['resource']
    
    def get_cost_client(self, user_id: int) -> Optional[CostManagementClient]:
        """Obtém cliente de Cost Management para um usuário"""
        if not self.is_user_authenticated(user_id):
            return None
        
        if user_id not in self.active_clients:
            self.active_clients[user_id] = {}
        
        if 'cost' not in self.active_clients[user_id]:
            credential = self.get_credential_object(user_id)
            self.active_clients[user_id]['cost'] = CostManagementClient(credential)
        
        return self.active_clients[user_id]['cost']
    
    def remove_user_credentials(self, user_id: int) -> bool:
        """Remove credenciais de um usuário"""
        try:
            # Limpar cache
            if user_id in self.active_clients:
                del self.active_clients[user_id]
            
            # Remover do banco
            return AzureCredentials.delete_by_user_id(user_id)
        except Exception as e:
            logger.error(f"Erro ao remover credenciais: {str(e)}")
            return False

class AzureResourceService:
    """Serviço para operações com recursos Azure"""
    
    def __init__(self, auth_service: AzureAuthService):
        self.auth_service = auth_service
    
    def list_resource_groups(self, user_id: int) -> Dict[str, Any]:
        """Lista resource groups da subscription"""
        try:
            client = self.auth_service.get_resource_client(user_id)
            if not client:
                return {'error': 'Credenciais não configuradas'}
            
            resource_groups = []
            for rg in client.resource_groups.list():
                resource_groups.append({
                    'name': rg.name,
                    'location': rg.location,
                    'tags': rg.tags or {}
                })
            
            return {
                'success': True,
                'resource_groups': resource_groups,
                'count': len(resource_groups)
            }
            
        except Exception as e:
            logger.error(f"Erro ao listar resource groups: {str(e)}")
            return {'error': str(e)}
    
    def list_resources(self, user_id: int, resource_group: str = None) -> Dict[str, Any]:
        """Lista recursos da subscription ou de um resource group específico"""
        try:
            client = self.auth_service.get_resource_client(user_id)
            if not client:
                return {'error': 'Credenciais não configuradas'}
            
            resources = []
            if resource_group:
                resource_list = client.resources.list_by_resource_group(resource_group)
            else:
                resource_list = client.resources.list()
            
            for resource in resource_list:
                resources.append({
                    'name': resource.name,
                    'type': resource.type,
                    'location': resource.location,
                    'resource_group': resource.id.split('/')[4],  # Extrair RG do ID
                    'tags': resource.tags or {}
                })
            
            return {
                'success': True,
                'resources': resources,
                'count': len(resources)
            }
            
        except Exception as e:
            logger.error(f"Erro ao listar recursos: {str(e)}")
            return {'error': str(e)}

class AzureCostService:
    """Serviço para operações de custos Azure"""
    
    def __init__(self, auth_service: AzureAuthService):
        self.auth_service = auth_service
    
    def get_current_month_costs(self, user_id: int) -> Dict[str, Any]:
        """Obtém custos do mês atual"""
        try:
            client = self.auth_service.get_cost_client(user_id)
            creds = self.auth_service.get_user_credentials(user_id)
            
            if not client or not creds:
                return {'error': 'Credenciais não configuradas'}
            
            # Definir escopo da subscription
            scope = f"/subscriptions/{creds.subscription_id}"
            
            # Período do mês atual
            now = datetime.now()
            start_date = now.replace(day=1).strftime('%Y-%m-%d')
            end_date = now.strftime('%Y-%m-%d')
            
            # Configurar query de custos
            query_definition = {
                "type": "ActualCost",
                "timeframe": "Custom",
                "timePeriod": {
                    "from": start_date,
                    "to": end_date
                },
                "dataset": {
                    "granularity": "Daily",
                    "aggregation": {
                        "totalCost": {
                            "name": "PreTaxCost",
                            "function": "Sum"
                        }
                    },
                    "grouping": [
                        {
                            "type": "Dimension",
                            "name": "ServiceName"
                        }
                    ]
                }
            }
            
            # Executar query
            result = client.query.usage(scope, query_definition)
            
            # Processar resultados
            daily_costs = []
            service_costs = {}
            total_cost = 0
            
            for row in result.rows:
                cost = float(row[0]) if row[0] else 0
                date = row[1]
                service = row[2] if len(row) > 2 else 'Unknown'
                
                total_cost += cost
                
                # Agrupar por data
                daily_costs.append({
                    'date': date,
                    'cost': cost,
                    'service': service
                })
                
                # Agrupar por serviço
                if service in service_costs:
                    service_costs[service] += cost
                else:
                    service_costs[service] = cost
            
            return {
                'success': True,
                'total_cost': round(total_cost, 2),
                'daily_costs': daily_costs,
                'service_costs': service_costs,
                'currency': 'USD',
                'period': f"{start_date} to {end_date}"
            }
            
        except Exception as e:
            logger.error(f"Erro ao obter custos: {str(e)}")
            return {'error': str(e)}

# Instâncias globais dos serviços
azure_auth_service = AzureAuthService()
azure_resource_service = AzureResourceService(azure_auth_service)
azure_cost_service = AzureCostService(azure_auth_service)

# Para compatibilidade com imports antigos
azure_service = azure_resource_service

