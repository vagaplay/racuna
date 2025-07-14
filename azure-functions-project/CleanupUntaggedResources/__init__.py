import azure.functions as func
import logging
import json
from datetime import datetime, timedelta
from azure.identity import DefaultAzureCredential, ClientSecretCredential
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.compute import ComputeManagementClient
from azure.mgmt.storage import StorageManagementClient
import os
import sys
sys.path.append('..')
from shared_config import AzureFunctionConfig

def main(req: func.HttpRequest) -> func.HttpResponse:
    """
    Azure Function para limpeza automática de recursos sem tags obrigatórias
    
    EXECUTA: Horário configurável (padrão: 19h) - fora do horário de trabalho
    FUNÇÃO: Identifica recursos sem tags obrigatórias e recursos órfãos
    AÇÃO: Limpeza automática baseada em configurações customizáveis
    """
    
    logging.info('=== LIMPEZA DE RECURSOS SEM TAGS (HORÁRIO CUSTOMIZÁVEL) ===')
    
    try:
        # Validar configurações
        AzureFunctionConfig.validate_config()
        
        # Verificar se é horário de verificação de tags (configurável)
        now = datetime.utcnow()
        scheduled_hour = AzureFunctionConfig.TAG_CHECK_HOUR
        
        # Verificar se é dia útil (segunda a sexta)
        if now.weekday() >= 5:  # 5 = sábado, 6 = domingo
            return func.HttpResponse(
                json.dumps({
                    'message': 'Limpeza de recursos não executada: Final de semana',
                    'current_day': now.strftime('%A'),
                    'scheduled_days': 'Segunda a Sexta',
                    'scheduled_hour': f'{scheduled_hour}:00',
                    'config': AzureFunctionConfig.get_config_summary()
                }),
                status_code=200,
                headers={'Content-Type': 'application/json'}
            )
        
        # Configurações de autenticação
        subscription_id = AzureFunctionConfig.SUBSCRIPTION_ID
        tenant_id = AzureFunctionConfig.TENANT_ID
        client_id = AzureFunctionConfig.CLIENT_ID
        client_secret = AzureFunctionConfig.CLIENT_SECRET
        
        # Configurar autenticação
        if client_id and client_secret and tenant_id:
            credential = ClientSecretCredential(
                tenant_id=tenant_id,
                client_id=client_id,
                client_secret=client_secret
            )
            logging.info("Usando Service Principal para autenticação")
        else:
            credential = DefaultAzureCredential()
            logging.info("Usando Default Azure Credential")
        
        # Clientes Azure
        resource_client = ResourceManagementClient(credential, subscription_id)
        compute_client = ComputeManagementClient(credential, subscription_id)
        storage_client = StorageManagementClient(credential, subscription_id)
        
        # Tags obrigatórias (configuráveis via environment)
        required_tags = os.getenv('REQUIRED_TAGS', 'Environment,Owner,Project').split(',')
        
        # Modo automático de deleção (configurável)
        auto_delete = req.params.get('auto_delete', 'false').lower() == 'true'
        
        # Resultados da limpeza
        cleanup_results = {
            'timestamp': datetime.utcnow().isoformat(),
            'execution_hour': now.hour,
            'scheduled_hour': scheduled_hour,
            'subscription_id': subscription_id,
            'required_tags': required_tags,
            'auto_delete_enabled': auto_delete,
            'resources_analyzed': 0,
            'resources_without_tags': [],
            'resources_deleted': [],
            'orphaned_resources': [],
            'errors': [],
            'summary': {},
            'config': AzureFunctionConfig.get_config_summary()
        }
        
        logging.info(f'Iniciando limpeza de recursos às {now.hour}:00 (agendado para {scheduled_hour}:00)')
        logging.info(f'Tags obrigatórias: {required_tags}')
        logging.info(f'Modo auto-delete: {auto_delete}')
        
        # 1. Analisar todos os recursos
        logging.info('Analisando recursos na subscription...')
        
        for resource in resource_client.resources.list():
            cleanup_results['resources_analyzed'] += 1
            
            try:
                # Verificar tags obrigatórias
                resource_tags = resource.tags or {}
                missing_tags = [tag.strip() for tag in required_tags if tag.strip() not in resource_tags]
                
                if missing_tags:
                    resource_info = {
                        'id': resource.id,
                        'name': resource.name,
                        'type': resource.type,
                        'location': resource.location,
                        'resource_group': resource.id.split('/')[4],
                        'missing_tags': missing_tags,
                        'current_tags': resource_tags
                    }
                    cleanup_results['resources_without_tags'].append(resource_info)
                    
                    # Verificar se recurso deve ser protegido (tem tag HoldLock)
                    if 'HoldLock' in resource_tags:
                        logging.info(f'Recurso {resource.name} protegido por HoldLock - não será removido')
                        resource_info['status'] = 'Protegido por HoldLock'
                        continue
                    
                    # Verificar se é um recurso órfão (lógica específica por tipo)
                    if is_orphaned_resource(resource, compute_client, storage_client):
                        cleanup_results['orphaned_resources'].append(resource_info)
                        resource_info['is_orphaned'] = True
                        
                        # Deletar recurso órfão (apenas se configurado para modo automático)
                        if auto_delete:
                            delete_result = delete_resource(resource_client, resource.id)
                            if delete_result['success']:
                                cleanup_results['resources_deleted'].append(resource_info)
                                resource_info['status'] = 'Deletado automaticamente'
                            else:
                                cleanup_results['errors'].append({
                                    'resource_id': resource.id,
                                    'error': delete_result['error']
                                })
                                resource_info['status'] = f'Erro na deleção: {delete_result["error"]}'
                        else:
                            resource_info['status'] = 'Marcado para deleção manual'
                    else:
                        resource_info['is_orphaned'] = False
                        resource_info['status'] = 'Sem tags obrigatórias mas não órfão'
                
            except Exception as e:
                logging.error(f"Erro ao analisar recurso {resource.id}: {str(e)}")
                cleanup_results['errors'].append({
                    'resource_id': resource.id,
                    'error': str(e)
                })
        
        # 2. Gerar resumo
        cleanup_results['summary'] = {
            'total_resources': cleanup_results['resources_analyzed'],
            'resources_without_tags': len(cleanup_results['resources_without_tags']),
            'orphaned_resources': len(cleanup_results['orphaned_resources']),
            'resources_deleted': len(cleanup_results['resources_deleted']),
            'errors_count': len(cleanup_results['errors'])
        }
        
        # 3. Salvar relatório (em produção, salvaria em Storage Account)
        logging.info(f"Limpeza concluída: {cleanup_results['summary']}")
        
        # 4. Enviar notificações (implementar conforme necessário)
        if cleanup_results['resources_deleted']:
            send_cleanup_notification(cleanup_results)
        
        # Log final
        logging.info(f'🎉 Limpeza de recursos concluída:')
        logging.info(f'   - Recursos analisados: {cleanup_results["resources_analyzed"]}')
        logging.info(f'   - Recursos sem tags: {len(cleanup_results["resources_without_tags"])}')
        logging.info(f'   - Recursos órfãos: {len(cleanup_results["orphaned_resources"])}')
        logging.info(f'   - Recursos deletados: {len(cleanup_results["resources_deleted"])}')
        logging.info(f'   - Erros: {len(cleanup_results["errors"])}')
        
        return func.HttpResponse(
            json.dumps(cleanup_results, indent=2),
            status_code=200,
            headers={'Content-Type': 'application/json'}
        )
        
    except Exception as e:
        error_msg = f"Erro na limpeza de recursos: {str(e)}"
        logging.error(error_msg)
        
        return func.HttpResponse(
            json.dumps({
                'error': error_msg,
                'timestamp': datetime.utcnow().isoformat(),
                'scheduled_hour': AzureFunctionConfig.TAG_CHECK_HOUR,
                'config': AzureFunctionConfig.get_config_summary()
            }),
            status_code=500,
            headers={'Content-Type': 'application/json'}
        )

def is_orphaned_resource(resource, compute_client, storage_client):
    """
    Determina se um recurso é órfão baseado em regras específicas
    """
    try:
        resource_type = resource.type.lower()
        
        # Discos não anexados
        if 'microsoft.compute/disks' in resource_type:
            disk = compute_client.disks.get(
                resource.id.split('/')[4],  # resource group
                resource.name
            )
            return disk.disk_state == 'Unattached'
        
        # NICs não anexadas
        elif 'microsoft.network/networkinterfaces' in resource_type:
            # Verificar se NIC está anexada a uma VM
            return not hasattr(resource, 'virtual_machine') or not resource.virtual_machine
        
        # IPs públicos não utilizados
        elif 'microsoft.network/publicipaddresses' in resource_type:
            # Verificar se IP está associado
            return not hasattr(resource, 'ip_configuration') or not resource.ip_configuration
        
        # Storage Accounts vazias (verificação mais complexa)
        elif 'microsoft.storage/storageaccounts' in resource_type:
            return is_empty_storage_account(storage_client, resource)
        
        # VMs paradas há muito tempo
        elif 'microsoft.compute/virtualmachines' in resource_type:
            return is_long_stopped_vm(compute_client, resource)
        
        return False
        
    except Exception as e:
        logging.warning(f"Erro ao verificar se recurso é órfão {resource.id}: {str(e)}")
        return False

def is_empty_storage_account(storage_client, resource):
    """
    Verifica se Storage Account está vazia
    """
    try:
        # Implementar lógica para verificar containers e blobs
        # Por segurança, retorna False por padrão
        return False
    except:
        return False

def is_long_stopped_vm(compute_client, resource):
    """
    Verifica se VM está parada há muito tempo
    """
    try:
        vm = compute_client.virtual_machines.get(
            resource.id.split('/')[4],  # resource group
            resource.name,
            expand='instanceView'
        )
        
        # Verificar se VM está deallocated há mais de 30 dias
        if vm.instance_view and vm.instance_view.statuses:
            for status in vm.instance_view.statuses:
                if 'PowerState/deallocated' in status.code:
                    # Em produção, verificaria timestamp do status
                    return True
        
        return False
    except:
        return False

def delete_resource(resource_client, resource_id):
    """
    Deleta um recurso Azure
    """
    try:
        # Em produção, implementaria delete real
        # Por segurança, apenas simula a deleção
        logging.info(f"SIMULANDO deleção do recurso: {resource_id}")
        
        return {
            'success': True,
            'message': f'Recurso {resource_id} deletado com sucesso (SIMULADO)'
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

def send_cleanup_notification(cleanup_results):
    """
    Envia notificação sobre limpeza realizada
    """
    try:
        # Implementar envio de email/Teams/Slack
        logging.info(f"Notificação de limpeza: {cleanup_results['summary']}")
        
        # Em produção, enviaria para:
        # - Email dos owners dos recursos
        # - Canal Teams/Slack
        # - Dashboard de monitoramento
        
    except Exception as e:
        logging.error(f"Erro ao enviar notificação: {str(e)}")

def main_timer(mytimer: func.TimerRequest) -> None:
    """
    Versão Timer Trigger para execução automática no horário configurado
    Configurar no function.json com expressão cron dinâmica baseada em AzureFunctionConfig.get_tag_check_cron()
    """
    logging.info('Timer trigger executado para limpeza de recursos')
    logging.info(f'Configuração atual: {AzureFunctionConfig.get_config_summary()}')
    
    # Simular HttpRequest para reutilizar a lógica
    fake_req = type('obj', (object,), {'params': {}})()
    
    try:
        response = main(fake_req)
        logging.info(f'Limpeza de recursos concluída: {response.status_code}')
    except Exception as e:
        logging.error(f'Erro na limpeza de recursos: {str(e)}')

