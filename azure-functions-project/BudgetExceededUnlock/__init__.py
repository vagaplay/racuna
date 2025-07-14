import azure.functions as func
import logging
import json
from datetime import datetime
from azure.identity import DefaultAzureCredential, ClientSecretCredential
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.resource.locks import ManagementLockClient
import os

def main(req: func.HttpRequest) -> func.HttpResponse:
    """
    Azure Function para remoção de locks quando budget é excedido
    
    BASEADO NO ARQUIVO: main.tf (PowerShell Runbook)
    TRIGGER: Budget excede o limite configurado (webhook)
    LÓGICA: 
    1. Se lock = "HoldLock" → Adiciona RG à lista permitida
    2. Se lock ≠ "HoldLock" → Remove o lock
    3. Permite exclusão de recursos (sem HoldLock)
    """
    
    logging.info('=== REMOÇÃO DE LOCKS POR BUDGET EXCEDIDO ===')
    
    try:
        # Parâmetros da requisição
        budget_limit = req.params.get('budget_limit')
        current_cost = req.params.get('current_cost')
        action = req.params.get('action', 'Disable')
        force_unlock = req.params.get('force_unlock', 'false').lower() == 'true'
        
        # Configurações de autenticação
        subscription_id = os.environ.get('AZURE_SUBSCRIPTION_ID')
        tenant_id = os.environ.get('AZURE_TENANT_ID')
        client_id = os.environ.get('AZURE_CLIENT_ID')
        client_secret = os.environ.get('AZURE_CLIENT_SECRET')
        
        if not subscription_id:
            raise ValueError("AZURE_SUBSCRIPTION_ID não configurado")
        
        # Lista de Resource Groups permitidos (configurável)
        allowed_rgs_env = os.environ.get('ALLOWED_RESOURCE_GROUPS', '[]')
        try:
            allowed_resource_groups = json.loads(allowed_rgs_env)
        except:
            allowed_resource_groups = []
        
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
        
        # Resultado da operação
        result = {
            'timestamp': datetime.utcnow().isoformat(),
            'trigger_reason': 'budget_exceeded',
            'action': action,
            'budget_limit': budget_limit,
            'current_cost': current_cost,
            'subscription_id': subscription_id,
            'allowed_resource_groups_initial': allowed_resource_groups.copy(),
            'allowed_resource_groups_final': [],
            'holdlock_found': [],
            'locks_removed': [],
            'locks_preserved': [],
            'errors': []
        }
        
        # Verificar se a ação é 'Disable'
        if action != "Disable":
            return func.HttpResponse(
                json.dumps({
                    'error': 'The action must be "Disable"',
                    'provided_action': action,
                    'valid_actions': ['Disable']
                }),
                status_code=400,
                headers={'Content-Type': 'application/json'}
            )
        
        logging.info(f'💰 Processando budget excedido. Ação: {action}')
        logging.info(f'📋 Resource Groups permitidos inicialmente: {allowed_resource_groups}')
        
        # ETAPA 1: Verificar locks e implementar lógica do PowerShell
        logging.info('🔍 Verificando locks existentes...')
        
        try:
            # Obter todos os locks da subscription
            all_locks = list(lock_client.management_locks.list_at_subscription_level())
            
            # Adicionar locks de resource groups
            for rg in resource_client.resource_groups.list():
                try:
                    rg_locks = list(lock_client.management_locks.list_at_resource_group_level(rg.name))
                    all_locks.extend(rg_locks)
                except Exception as e:
                    logging.debug(f'Erro ao listar locks do RG {rg.name}: {str(e)}')
            
            # Adicionar locks de recursos individuais
            for resource in resource_client.resources.list():
                try:
                    resource_locks = list(lock_client.management_locks.list_at_resource_level(
                        resource_group_name=resource.id.split('/')[4],
                        resource_provider_namespace=resource.type.split('/')[0],
                        resource_type=resource.type.split('/')[1],
                        resource_name=resource.name
                    ))
                    all_locks.extend(resource_locks)
                except Exception as e:
                    logging.debug(f'Erro ao listar locks do recurso {resource.name}: {str(e)}')
            
            logging.info(f'📋 Total de locks encontrados: {len(all_locks)}')
            
        except Exception as e:
            logging.error(f'Erro ao listar locks: {str(e)}')
            all_locks = []
        
        # ETAPA 2: Implementar lógica do PowerShell
        # foreach ($lock in $locks) {
        #     if ($lock.Name -eq "HoldLock") {  
        #         # Add the resource group with 'HoldLock' lock to the allowed list.
        #         $resourceGroupName = ($lock.ResourceId -split "/")[4]
        #         if ($allowedResourceGroups -notcontains $resourceGroupName) {
        #             $allowedResourceGroups += $resourceGroupName
        #         }
        #     } else {
        #         Remove-AzResourceLock -LockId $lock.LockId -Force
        #     }                   
        # }
        
        for lock in all_locks:
            try:
                if lock.name == "HoldLock":
                    # Extrair nome do resource group do scope do lock
                    scope_parts = lock.scope.split('/')
                    if len(scope_parts) >= 5 and scope_parts[3] == 'resourceGroups':
                        resource_group_name = scope_parts[4]
                        
                        if resource_group_name not in allowed_resource_groups:
                            allowed_resource_groups.append(resource_group_name)
                            result['holdlock_found'].append({
                                'lock_name': lock.name,
                                'resource_group': resource_group_name,
                                'scope': lock.scope,
                                'action': 'added_to_allowed_list'
                            })
                            logging.info(f'🔒 Resource group: {resource_group_name} added to the allowed list because it contains the "HoldLock"')
                        else:
                            result['holdlock_found'].append({
                                'lock_name': lock.name,
                                'resource_group': resource_group_name,
                                'scope': lock.scope,
                                'action': 'already_in_allowed_list'
                            })
                            logging.info(f'🔒 Resource group: {resource_group_name} already in allowed list (HoldLock)')
                    else:
                        result['holdlock_found'].append({
                            'lock_name': lock.name,
                            'scope': lock.scope,
                            'action': 'scope_not_resource_group',
                            'note': 'HoldLock found but not at resource group level'
                        })
                        logging.warning(f'⚠️ HoldLock encontrado mas não é de resource group: {lock.scope}')
                
                else:
                    # Remover todos os outros locks (que não são HoldLock)
                    logging.info(f'🗑️ Removing lock: {lock.name} to proceed with the deletion of the resources.')
                    
                    try:
                        # Determinar o método de remoção baseado no scope
                        if '/subscriptions/' in lock.scope and '/resourceGroups/' not in lock.scope:
                            # Lock da subscription
                            lock_client.management_locks.delete_at_subscription_level(lock.name)
                        elif '/resourceGroups/' in lock.scope and '/providers/' not in lock.scope:
                            # Lock de resource group
                            rg_name = lock.scope.split('/')[4]
                            lock_client.management_locks.delete_at_resource_group_level(rg_name, lock.name)
                        else:
                            # Lock de recurso individual
                            scope_parts = lock.scope.split('/')
                            if len(scope_parts) >= 9:
                                rg_name = scope_parts[4]
                                provider = scope_parts[6]
                                resource_type = scope_parts[7]
                                resource_name = scope_parts[8]
                                
                                lock_client.management_locks.delete_at_resource_level(
                                    resource_group_name=rg_name,
                                    resource_provider_namespace=provider,
                                    resource_type=resource_type,
                                    resource_name=resource_name,
                                    lock_name=lock.name
                                )
                        
                        result['locks_removed'].append({
                            'name': lock.name,
                            'level': lock.level,
                            'scope': lock.scope,
                            'notes': lock.notes or 'Sem notas'
                        })
                        
                        logging.info(f'✅ Lock {lock.name} removido com sucesso')
                        
                    except Exception as e:
                        error_msg = f'Erro ao remover lock {lock.name}: {str(e)}'
                        logging.error(error_msg)
                        result['errors'].append({
                            'lock_name': lock.name,
                            'scope': lock.scope,
                            'error': str(e)
                        })
                        
                        # Adicionar à lista de preservados (por erro)
                        result['locks_preserved'].append({
                            'name': lock.name,
                            'level': lock.level,
                            'scope': lock.scope,
                            'reason': f'Error during removal: {str(e)}'
                        })
                
            except Exception as e:
                error_msg = f'Erro ao processar lock {lock.name}: {str(e)}'
                logging.error(error_msg)
                result['errors'].append({
                    'lock_name': lock.name,
                    'error': str(e)
                })
        
        # ETAPA 3: Criar lock de proteção na subscription
        try:
            logging.info('🔐 Adding ReadOnly lock to the subscription...')
            
            lock_name = "Prevent-Spending-BudgetControl"
            notes = "Temporary lock to prevent spending costs, the subscription's budget has been exceeded."
            
            lock_client.management_locks.create_or_update_at_subscription_level(
                lock_name=lock_name,
                parameters={
                    'level': 'ReadOnly',
                    'notes': notes
                }
            )
            
            result['subscription_lock'] = {
                'name': lock_name,
                'level': 'ReadOnly',
                'notes': notes,
                'created': datetime.utcnow().isoformat()
            }
            
            logging.info(f'✅ ReadOnly lock "{lock_name}" criado na subscription')
            
        except Exception as e:
            logging.error(f'Erro ao criar lock de proteção na subscription: {str(e)}')
            result['errors'].append({
                'resource': 'subscription',
                'action': 'create_protection_lock',
                'error': str(e)
            })
        
        # ETAPA 4: Finalizar resultado
        result['allowed_resource_groups_final'] = allowed_resource_groups
        result['summary'] = {
            'total_locks_processed': len(all_locks),
            'holdlocks_found': len(result['holdlock_found']),
            'locks_removed': len(result['locks_removed']),
            'locks_preserved': len(result['locks_preserved']),
            'errors_count': len(result['errors']),
            'allowed_rgs_added': len(allowed_resource_groups) - len(result['allowed_resource_groups_initial']),
            'operation_successful': len(result['errors']) == 0,
            'ready_for_resource_deletion': True
        }
        
        # Log final
        logging.info(f'🎉 Processamento concluído:')
        logging.info(f'   • HoldLocks encontrados: {result["summary"]["holdlocks_found"]}')
        logging.info(f'   • Locks removidos: {result["summary"]["locks_removed"]}')
        logging.info(f'   • RGs adicionados à lista permitida: {result["summary"]["allowed_rgs_added"]}')
        logging.info(f'   • Erros: {result["summary"]["errors_count"]}')
        logging.info(f'✅ Subscription {subscription_id} processada para exclusão de recursos')
        
        return func.HttpResponse(
            json.dumps(result, indent=2),
            status_code=200,
            headers={'Content-Type': 'application/json'}
        )
        
    except Exception as e:
        error_msg = f'Erro no processamento de budget excedido: {str(e)}'
        logging.error(error_msg)
        
        return func.HttpResponse(
            json.dumps({
                'error': error_msg,
                'timestamp': datetime.utcnow().isoformat(),
                'trigger_reason': 'budget_exceeded',
                'action': action
            }),
            status_code=500,
            headers={'Content-Type': 'application/json'}
        )

