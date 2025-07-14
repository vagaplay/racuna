"""
Serviço para ações reais no Azure
Implementa operações que realmente executam na subscription Azure
"""

import logging
from typing import Dict, Any, List, Optional
from azure.identity import ClientSecretCredential
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.resource.locks import ManagementLockClient
from azure.mgmt.compute import ComputeManagementClient
from azure.mgmt.authorization import AuthorizationManagementClient
from azure.core.exceptions import ClientAuthenticationError, HttpResponseError
from src.services.azure_service import azure_auth_service

logger = logging.getLogger(__name__)

class AzureActionsService:
    """Serviço para executar ações reais no Azure"""
    
    def __init__(self):
        self.auth_service = azure_auth_service
    
    def _get_clients(self, user_id: int) -> Dict[str, Any]:
        """Obtém clientes Azure autenticados para o usuário"""
        try:
            if not self.auth_service.is_user_authenticated(user_id):
                raise Exception("Usuário não tem credenciais Azure configuradas")
            
            creds = self.auth_service.get_user_credentials(user_id)
            
            credential = ClientSecretCredential(
                tenant_id=creds.tenant_id,
                client_id=creds.client_id,
                client_secret=creds.get_client_secret()
            )
            
            return {
                'credential': credential,
                'subscription_id': creds.subscription_id,
                'resource_client': ResourceManagementClient(credential, creds.subscription_id),
                'compute_client': ComputeManagementClient(credential, creds.subscription_id),
                'auth_client': AuthorizationManagementClient(credential, creds.subscription_id),
                'lock_client': ManagementLockClient(credential, creds.subscription_id)
            }
        except Exception as e:
            logger.error(f"Erro ao obter clientes Azure: {str(e)}")
            raise
    
    def create_resource_group_lock(self, user_id: int, lock_name: str, resource_group: str, 
                                 level: str = "CanNotDelete", notes: str = None) -> Dict[str, Any]:
        """Cria um lock em um Resource Group específico"""
        try:
            clients = self._get_clients(user_id)
            lock_client = clients['lock_client']
            
            # Parâmetros do lock
            lock_params = {
                'level': level,
                'notes': notes or f"Lock criado pelo BOLT Dashboard - {datetime.utcnow().isoformat()}"
            }
            
            logger.info(f"Criando lock '{lock_name}' no Resource Group '{resource_group}' com nível '{level}'")
            
            # Criar lock no Resource Group
            result = lock_client.management_locks.create_or_update_at_resource_group_level(
                resource_group_name=resource_group,
                lock_name=lock_name,
                parameters=lock_params
            )
            
            logger.info(f"Lock '{lock_name}' criado com sucesso no Resource Group '{resource_group}'")
            
            return {
                'success': True,
                'message': f'Lock "{lock_name}" criado com sucesso no Resource Group "{resource_group}"',
                'lock_name': result.name,
                'level': result.level,
                'scope': f'Resource Group: {resource_group}',
                'notes': result.notes,
                'id': result.id
            }
            
        except HttpResponseError as e:
            if e.status_code == 409:
                return {
                    'success': False,
                    'error': f'Lock "{lock_name}" já existe no Resource Group "{resource_group}"'
                }
            elif e.status_code == 404:
                return {
                    'success': False,
                    'error': f'Resource Group "{resource_group}" não encontrado'
                }
            else:
                error_msg = f"Erro HTTP ao criar lock: {e.message}"
                logger.error(error_msg)
                return {
                    'success': False,
                    'error': error_msg
                }
        except Exception as e:
            error_msg = f"Erro ao criar lock no Resource Group: {str(e)}"
            logger.error(error_msg)
            logger.error(f"Detalhes: {repr(e)}")
            return {
                'success': False,
                'error': error_msg
            }

    def create_subscription_lock(self, user_id: int, lock_name: str = "Prevent-Spending-BudgetControl", 
                               level: str = "CanNotDelete", notes: str = None) -> Dict[str, Any]:
        """Cria um lock de prevenção de gastos na subscription"""
        try:
            logger.info(f"Iniciando criação de lock '{lock_name}' para usuário {user_id}")
            
            clients = self._get_clients(user_id)
            lock_client = clients['lock_client']
            subscription_id = clients['subscription_id']
            
            logger.info(f"Clientes obtidos com sucesso. Subscription: {subscription_id}")
            
            # Definir parâmetros do lock
            from azure.mgmt.resource.locks.models import ManagementLockObject
            
            lock_parameters = ManagementLockObject(
                level='CanNotDelete',  # Impede deleção de recursos
                notes='Lock criado pelo BOLT Dashboard para controle de gastos'
            )
            
            logger.info(f"Parâmetros do lock definidos: {lock_parameters}")
            
            # Criar lock na subscription
            logger.info(f"Tentando criar lock na subscription {subscription_id}")
            
            lock = lock_client.management_locks.create_or_update_at_subscription_level(
                lock_name=lock_name,
                parameters=lock_parameters
            )
            
            logger.info(f"Lock '{lock_name}' criado com sucesso na subscription {subscription_id}")
            
            return {
                'success': True,
                'message': f'Lock "{lock_name}" criado com sucesso',
                'lock_id': lock.id,
                'lock_name': lock.name,
                'level': lock.level,
                'notes': lock.notes
            }
            
        except HttpResponseError as e:
            error_msg = f"Erro HTTP ao criar lock: {e.message}"
            logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg,
                'details': str(e)
            }
        except Exception as e:
            error_msg = f"Erro ao criar lock: {str(e)}"
            logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg
            }
    
    def remove_subscription_lock(self, user_id: int, lock_name: str = "Prevent-Spending-BudgetControl") -> Dict[str, Any]:
        """Remove um lock da subscription ou resource group"""
        try:
            clients = self._get_clients(user_id)
            lock_client = clients['lock_client']
            
            logger.info(f"Tentando remover lock '{lock_name}'")
            
            # Primeiro, listar todos os locks para encontrar o correto
            all_locks = list(lock_client.management_locks.list_at_subscription_level())
            
            target_lock = None
            for lock in all_locks:
                if lock.name == lock_name:
                    target_lock = lock
                    break
            
            if not target_lock:
                return {
                    'success': False,
                    'error': f'Lock "{lock_name}" não encontrado'
                }
            
            # Determinar o escopo do lock e remover adequadamente
            lock_id = target_lock.id
            logger.info(f"Lock encontrado com ID: {lock_id}")
            
            # Usar delete_by_scope que é mais confiável
            # Extrair o scope do ID do lock (remover a parte do lock)
            scope = '/'.join(lock_id.split('/')[:-4])  # Remove /providers/Microsoft.Authorization/locks/nome
            
            logger.info(f"Removendo lock usando scope: {scope}")
            lock_client.management_locks.delete_by_scope(
                scope=scope,
                lock_name=lock_name
            )
            
            logger.info(f"Lock '{lock_name}' removido com sucesso")
            
            return {
                'success': True,
                'message': f'Lock "{lock_name}" removido com sucesso'
            }
            
        except HttpResponseError as e:
            if e.status_code == 404:
                return {
                    'success': False,
                    'error': f'Lock "{lock_name}" não encontrado'
                }
            else:
                error_msg = f"Erro HTTP ao remover lock: {e.message}"
                logger.error(error_msg)
                return {
                    'success': False,
                    'error': error_msg
                }
        except Exception as e:
            error_msg = f"Erro ao remover lock: {str(e)}"
            logger.error(error_msg)
            logger.error(f"Detalhes: {repr(e)}")
            return {
                'success': False,
                'error': error_msg
            }
    
    def list_subscription_locks(self, user_id: int) -> Dict[str, Any]:
        """Lista todos os locks da subscription"""
        try:
            clients = self._get_clients(user_id)
            lock_client = clients['lock_client']
            
            # Listar locks da subscription
            locks = list(lock_client.management_locks.list_at_subscription_level())
            
            locks_data = []
            for lock in locks:
                locks_data.append({
                    'id': lock.id,
                    'name': lock.name,
                    'level': lock.level,
                    'notes': lock.notes
                })
            
            return {
                'success': True,
                'locks': locks_data,
                'count': len(locks_data)
            }
            
        except Exception as e:
            error_msg = f"Erro ao listar locks: {str(e)}"
            logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg,
                'locks': [],
                'count': 0
            }
    
    def list_virtual_machines(self, user_id: int) -> Dict[str, Any]:
        """Lista todas as VMs da subscription"""
        try:
            clients = self._get_clients(user_id)
            compute_client = clients['compute_client']
            
            # Listar VMs
            vms = list(compute_client.virtual_machines.list_all())
            
            vms_data = []
            for vm in vms:
                # Obter status da VM
                instance_view = compute_client.virtual_machines.instance_view(
                    resource_group_name=vm.id.split('/')[4],  # Extrair resource group do ID
                    vm_name=vm.name
                )
                
                # Determinar status
                power_state = "Unknown"
                for status in instance_view.statuses:
                    if status.code.startswith('PowerState/'):
                        power_state = status.code.replace('PowerState/', '')
                        break
                
                vms_data.append({
                    'id': vm.id,
                    'name': vm.name,
                    'location': vm.location,
                    'resource_group': vm.id.split('/')[4],
                    'vm_size': vm.hardware_profile.vm_size,
                    'os_type': vm.storage_profile.os_disk.os_type.value if vm.storage_profile.os_disk.os_type else 'Unknown',
                    'power_state': power_state,
                    'tags': vm.tags or {}
                })
            
            return {
                'success': True,
                'vms': vms_data,
                'count': len(vms_data)
            }
            
        except Exception as e:
            error_msg = f"Erro ao listar VMs: {str(e)}"
            logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg,
                'vms': [],
                'count': 0
            }
    
    def shutdown_virtual_machine(self, user_id: int, resource_group: str, vm_name: str) -> Dict[str, Any]:
        """Desliga uma VM específica"""
        try:
            clients = self._get_clients(user_id)
            compute_client = clients['compute_client']
            
            # Desligar VM
            operation = compute_client.virtual_machines.begin_power_off(
                resource_group_name=resource_group,
                vm_name=vm_name
            )
            
            # Aguardar conclusão (opcional - pode ser assíncrono)
            operation.wait()
            
            logger.info(f"VM '{vm_name}' desligada com sucesso")
            
            return {
                'success': True,
                'message': f'VM "{vm_name}" desligada com sucesso',
                'vm_name': vm_name,
                'resource_group': resource_group,
                'action': 'shutdown'
            }
            
        except Exception as e:
            error_msg = f"Erro ao desligar VM: {str(e)}"
            logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg
            }
    
    def start_virtual_machine(self, user_id: int, resource_group: str, vm_name: str) -> Dict[str, Any]:
        """Liga uma VM específica"""
        try:
            clients = self._get_clients(user_id)
            compute_client = clients['compute_client']
            
            # Ligar VM
            operation = compute_client.virtual_machines.begin_start(
                resource_group_name=resource_group,
                vm_name=vm_name
            )
            
            # Aguardar conclusão (opcional - pode ser assíncrono)
            operation.wait()
            
            logger.info(f"VM '{vm_name}' ligada com sucesso")
            
            return {
                'success': True,
                'message': f'VM "{vm_name}" ligada com sucesso',
                'vm_name': vm_name,
                'resource_group': resource_group,
                'action': 'start'
            }
            
        except Exception as e:
            error_msg = f"Erro ao ligar VM: {str(e)}"
            logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg
            }
    
    def apply_tags_to_resource(self, user_id: int, resource_id: str, tags: Dict[str, str]) -> Dict[str, Any]:
        """Aplica tags a um recurso específico"""
        try:
            clients = self._get_clients(user_id)
            resource_client = clients['resource_client']
            
            # Obter recurso atual
            resource = resource_client.resources.get_by_id(
                resource_id=resource_id,
                api_version='2021-04-01'
            )
            
            # Mesclar tags existentes com novas
            current_tags = resource.tags or {}
            updated_tags = {**current_tags, **tags}
            
            # Atualizar recurso com novas tags
            resource.tags = updated_tags
            
            updated_resource = resource_client.resources.update_by_id(
                resource_id=resource_id,
                api_version='2021-04-01',
                parameters=resource
            )
            
            logger.info(f"Tags aplicadas ao recurso {resource_id}")
            
            return {
                'success': True,
                'message': 'Tags aplicadas com sucesso',
                'resource_id': resource_id,
                'applied_tags': tags,
                'all_tags': updated_resource.tags
            }
            
        except Exception as e:
            error_msg = f"Erro ao aplicar tags: {str(e)}"
            logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg
            }

# Instância global do serviço
azure_actions_service = AzureActionsService()

