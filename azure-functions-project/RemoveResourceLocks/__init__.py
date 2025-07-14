import azure.functions as func
import logging
import json
from datetime import datetime, timedelta
from azure.identity import DefaultAzureCredential, ClientSecretCredential
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.resource.locks import ManagementLockClient
import os

def main(req: func.HttpRequest) -> func.HttpResponse:
    """
    Azure Function para remoção automática de locks de recursos
    
    Funcionalidades:
    - Remove locks expirados
    - Remove locks de recursos deletados
    - Gera relatório de locks removidos
    - Notifica sobre locks críticos
    """
    
    logging.info('Iniciando remoção automática de locks Azure')
    
    try:
        # Configurações
        subscription_id = os.environ.get('AZURE_SUBSCRIPTION_ID')
        tenant_id = os.environ.get('AZURE_TENANT_ID')
        client_id = os.environ.get('AZURE_CLIENT_ID')
        client_secret = os.environ.get('AZURE_CLIENT_SECRET')
        
        # Configurar autenticação
        if client_id and client_secret and tenant_id:
            credential = ClientSecretCredential(
                tenant_id=tenant_id,
                client_id=client_id,
                client_secret=client_secret
            )
        else:
            credential = DefaultAzureCredential()
        
        # Clientes Azure
        resource_client = ResourceManagementClient(credential, subscription_id)
        lock_client = ManagementLockClient(credential, subscription_id)
        
        # Resultados da operação
        lock_results = {
            'timestamp': datetime.utcnow().isoformat(),
            'locks_analyzed': 0,
            'expired_locks': [],
            'orphaned_locks': [],
            'locks_removed': [],
            'critical_locks': [],
            'errors': [],
            'summary': {}
        }
        
        # Parâmetros da requisição
        auto_remove = req.params.get('auto_remove', 'false').lower() == 'true'
        max_age_days = int(req.params.get('max_age_days', '90'))
        
        # 1. Analisar todos os locks na subscription
        logging.info('Analisando locks na subscription...')
        
        for lock in lock_client.management_locks.list_at_subscription_level():
            lock_results['locks_analyzed'] += 1
            
            try:
                lock_info = {
                    'id': lock.id,
                    'name': lock.name,
                    'level': lock.level,
                    'notes': lock.notes,
                    'scope': lock.scope,
                    'created_date': getattr(lock, 'created_date', None),
                    'created_by': getattr(lock, 'created_by', None)
                }
                
                # 2. Verificar se lock é expirado
                if is_expired_lock(lock, max_age_days):
                    lock_results['expired_locks'].append(lock_info)
                    
                    if auto_remove:
                        remove_result = remove_lock(lock_client, lock)
                        if remove_result['success']:
                            lock_results['locks_removed'].append(lock_info)
                        else:
                            lock_results['errors'].append({
                                'lock_id': lock.id,
                                'error': remove_result['error']
                            })
                
                # 3. Verificar se lock é órfão (recurso não existe mais)
                elif is_orphaned_lock(resource_client, lock):
                    lock_results['orphaned_locks'].append(lock_info)
                    
                    if auto_remove:
                        remove_result = remove_lock(lock_client, lock)
                        if remove_result['success']:
                            lock_results['locks_removed'].append(lock_info)
                        else:
                            lock_results['errors'].append({
                                'lock_id': lock.id,
                                'error': remove_result['error']
                            })
                
                # 4. Identificar locks críticos (CanNotDelete em recursos importantes)
                elif is_critical_lock(lock):
                    lock_results['critical_locks'].append(lock_info)
                
            except Exception as e:
                logging.error(f"Erro ao analisar lock {lock.id}: {str(e)}")
                lock_results['errors'].append({
                    'lock_id': lock.id,
                    'error': str(e)
                })
        
        # 5. Analisar locks em resource groups
        for rg in resource_client.resource_groups.list():
            try:
                for lock in lock_client.management_locks.list_at_resource_group_level(rg.name):
                    lock_results['locks_analyzed'] += 1
                    
                    lock_info = {
                        'id': lock.id,
                        'name': lock.name,
                        'level': lock.level,
                        'notes': lock.notes,
                        'scope': lock.scope,
                        'resource_group': rg.name
                    }
                    
                    # Aplicar mesma lógica de verificação
                    if is_expired_lock(lock, max_age_days):
                        lock_results['expired_locks'].append(lock_info)
                        
                        if auto_remove:
                            remove_result = remove_lock_from_rg(lock_client, rg.name, lock)
                            if remove_result['success']:
                                lock_results['locks_removed'].append(lock_info)
                    
            except Exception as e:
                logging.warning(f"Erro ao analisar locks do RG {rg.name}: {str(e)}")
        
        # 6. Gerar resumo
        lock_results['summary'] = {
            'total_locks': lock_results['locks_analyzed'],
            'expired_locks': len(lock_results['expired_locks']),
            'orphaned_locks': len(lock_results['orphaned_locks']),
            'locks_removed': len(lock_results['locks_removed']),
            'critical_locks': len(lock_results['critical_locks']),
            'errors_count': len(lock_results['errors'])
        }
        
        # 7. Enviar notificações se necessário
        if lock_results['locks_removed'] or lock_results['critical_locks']:
            send_lock_notification(lock_results)
        
        logging.info(f"Remoção de locks concluída: {lock_results['summary']}")
        
        return func.HttpResponse(
            json.dumps(lock_results, indent=2, default=str),
            status_code=200,
            headers={'Content-Type': 'application/json'}
        )
        
    except Exception as e:
        logging.error(f"Erro na remoção de locks: {str(e)}")
        return func.HttpResponse(
            json.dumps({
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }),
            status_code=500,
            headers={'Content-Type': 'application/json'}
        )

def is_expired_lock(lock, max_age_days):
    """
    Verifica se lock está expirado baseado na idade
    """
    try:
        # Se não tem data de criação, considera como não expirado
        if not hasattr(lock, 'created_date') or not lock.created_date:
            return False
        
        # Calcular idade do lock
        created_date = lock.created_date
        if isinstance(created_date, str):
            created_date = datetime.fromisoformat(created_date.replace('Z', '+00:00'))
        
        age = datetime.utcnow() - created_date.replace(tzinfo=None)
        
        return age.days > max_age_days
        
    except Exception as e:
        logging.warning(f"Erro ao verificar expiração do lock: {str(e)}")
        return False

def is_orphaned_lock(resource_client, lock):
    """
    Verifica se lock é órfão (recurso não existe mais)
    """
    try:
        # Extrair resource ID do scope do lock
        scope = lock.scope
        
        # Se é lock de subscription, não é órfão
        if '/subscriptions/' in scope and scope.count('/') <= 2:
            return False
        
        # Se é lock de resource group
        if '/resourceGroups/' in scope and '/providers/' not in scope:
            rg_name = scope.split('/resourceGroups/')[1].split('/')[0]
            try:
                resource_client.resource_groups.get(rg_name)
                return False  # Resource group existe
            except:
                return True   # Resource group não existe
        
        # Se é lock de recurso específico
        if '/providers/' in scope:
            try:
                # Tentar obter o recurso
                resource_client.resources.get_by_id(scope, api_version='2021-04-01')
                return False  # Recurso existe
            except:
                return True   # Recurso não existe
        
        return False
        
    except Exception as e:
        logging.warning(f"Erro ao verificar se lock é órfão: {str(e)}")
        return False

def is_critical_lock(lock):
    """
    Identifica locks críticos que precisam de atenção especial
    """
    try:
        # Locks CanNotDelete em recursos críticos
        if lock.level == 'CanNotDelete':
            scope = lock.scope.lower()
            
            # Recursos críticos que merecem atenção
            critical_resources = [
                'microsoft.keyvault',
                'microsoft.storage',
                'microsoft.sql',
                'microsoft.network/virtualnetworks',
                'microsoft.compute/virtualmachines'
            ]
            
            return any(resource_type in scope for resource_type in critical_resources)
        
        return False
        
    except Exception as e:
        logging.warning(f"Erro ao verificar se lock é crítico: {str(e)}")
        return False

def remove_lock(lock_client, lock):
    """
    Remove um lock da subscription
    """
    try:
        # Em produção, removeria o lock real
        # Por segurança, apenas simula a remoção
        logging.info(f"SIMULANDO remoção do lock: {lock.id}")
        
        # lock_client.management_locks.delete_at_subscription_level(lock.name)
        
        return {
            'success': True,
            'message': f'Lock {lock.name} removido com sucesso (SIMULADO)'
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

def remove_lock_from_rg(lock_client, resource_group_name, lock):
    """
    Remove um lock de resource group
    """
    try:
        # Em produção, removeria o lock real
        logging.info(f"SIMULANDO remoção do lock {lock.name} do RG {resource_group_name}")
        
        # lock_client.management_locks.delete_at_resource_group_level(resource_group_name, lock.name)
        
        return {
            'success': True,
            'message': f'Lock {lock.name} removido do RG {resource_group_name} (SIMULADO)'
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

def send_lock_notification(lock_results):
    """
    Envia notificação sobre locks removidos
    """
    try:
        logging.info(f"Notificação de locks: {lock_results['summary']}")
        
        # Em produção, enviaria notificações para:
        # - Administradores Azure
        # - Owners dos recursos
        # - Canal de monitoramento
        
    except Exception as e:
        logging.error(f"Erro ao enviar notificação de locks: {str(e)}")

