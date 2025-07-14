import azure.functions as func
import logging
import json
from datetime import datetime
from azure.identity import DefaultAzureCredential, ClientSecretCredential
from azure.mgmt.resource.locks import ManagementLockClient
import os
import sys
sys.path.append('..')
from shared_config import AzureFunctionConfig

def main(req: func.HttpRequest) -> func.HttpResponse:
    """
    Azure Function para verificação e remoção de lock da subscription
    
    BASEADO NO ARQUIVO: Deleteaccountlock.sh
    EXECUTA: Dia configurável (padrão: dia 02) - customizável via LOCK_CHECK_DAY
    FUNÇÃO: Verifica se existe lock configurado na subscription
    AÇÃO: Remove APENAS este lock específico (se existir)
    """
    
    logging.info('=== VERIFICAÇÃO DE LOCK DA SUBSCRIPTION (DIA CUSTOMIZÁVEL) ===')
    
    try:
        # Validar configurações
        AzureFunctionConfig.validate_config()
        
        # Verificar se hoje é o dia agendado (configurável)
        today = datetime.utcnow()
        scheduled_day = AzureFunctionConfig.LOCK_CHECK_DAY
        
        if today.day != scheduled_day:
            return func.HttpResponse(
                json.dumps({
                    'message': f'Função executada fora do dia agendado. Hoje: {today.day}, Agendado: {scheduled_day}',
                    'scheduled_day': scheduled_day,
                    'current_day': today.day,
                    'next_execution': f'{scheduled_day:02d}/{today.month + 1 if today.month < 12 else 1}/{today.year if today.month < 12 else today.year + 1}',
                    'note': 'Baseado no arquivo Deleteaccountlock.sh original - Dia customizável',
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
        
        # Cliente para gerenciar locks
        lock_client = ManagementLockClient(credential, subscription_id)
        
        # Nome do lock configurável
        target_lock_name = AzureFunctionConfig.BUDGET_LOCK_NAME
        
        # Resultado da operação
        result = {
            'timestamp': datetime.utcnow().isoformat(),
            'execution_day': today.day,
            'scheduled_day': scheduled_day,
            'subscription_id': subscription_id,
            'target_lock_name': target_lock_name,
            'lock_found': False,
            'lock_removed': False,
            'message': '',
            'error': None,
            'config': AzureFunctionConfig.get_config_summary()
        }
        
        logging.info(f'Verificando lock "{target_lock_name}" na subscription: {subscription_id}')
        logging.info(f'Configuração: Dia {scheduled_day} do mês às 8h')
        
        # Listar todos os locks da subscription
        subscription_locks = list(lock_client.management_locks.list_at_subscription_level())
        
        # Procurar especificamente pelo lock configurado
        target_lock = None
        for lock in subscription_locks:
            if lock.name == target_lock_name:
                target_lock = lock
                result['lock_found'] = True
                break
        
        if not target_lock:
            result['message'] = f"The lock '{target_lock_name}' was not found. Nothing to remove."
            logging.info(f'✅ Lock "{target_lock_name}" não encontrado')
        else:
            logging.info(f'🔒 Lock "{target_lock_name}" encontrado. Removendo...')
            
            try:
                # REMOVER O LOCK ESPECÍFICO DA SUBSCRIPTION
                lock_client.management_locks.delete_at_subscription_level(target_lock.name)
                
                result['lock_removed'] = True
                result['message'] = f"Lock '{target_lock_name}' found and successfully removed!"
                result['lock_details'] = {
                    'name': target_lock.name,
                    'level': target_lock.level,
                    'notes': target_lock.notes or 'Sem notas',
                    'scope': target_lock.scope
                }
                
                logging.info(f'✅ Lock "{target_lock_name}" removido com sucesso')
                
                # Verificar se foi realmente removido
                try:
                    remaining_locks = list(lock_client.management_locks.list_at_subscription_level())
                    still_exists = any(lock.name == target_lock_name for lock in remaining_locks)
                    
                    if not still_exists:
                        result['verification'] = 'Lock successfully removed and verified'
                        logging.info('✅ Verificação: Lock foi removido com sucesso')
                    else:
                        result['verification'] = 'Warning: Lock still exists after removal attempt'
                        logging.warning('⚠️ Aviso: Lock ainda existe após tentativa de remoção')
                        
                except Exception as e:
                    result['verification'] = f'Could not verify removal: {str(e)}'
                    logging.warning(f'⚠️ Não foi possível verificar remoção: {str(e)}')
                
            except Exception as e:
                error_msg = f'Erro ao remover lock "{target_lock_name}": {str(e)}'
                logging.error(error_msg)
                result['error'] = str(e)
                result['message'] = f'Error removing the lock. Please check the subscription. Error: {str(e)}'
        
        # Log final baseado no arquivo original
        if result['lock_removed']:
            logging.info('🎉 Verificação concluída: Lock removido com sucesso!')
        elif result['lock_found']:
            logging.error('❌ Verificação concluída: Erro ao remover lock')
        else:
            logging.info('✅ Verificação concluída: Nenhum lock encontrado')
        
        return func.HttpResponse(
            json.dumps(result, indent=2),
            status_code=200,
            headers={'Content-Type': 'application/json'}
        )
        
    except Exception as e:
        error_msg = f'Erro na verificação de lock da subscription: {str(e)}'
        logging.error(error_msg)
        
        return func.HttpResponse(
            json.dumps({
                'error': error_msg,
                'timestamp': datetime.utcnow().isoformat(),
                'execution_day': datetime.utcnow().day,
                'scheduled_day': AzureFunctionConfig.LOCK_CHECK_DAY,
                'target_lock_name': AzureFunctionConfig.BUDGET_LOCK_NAME,
                'config': AzureFunctionConfig.get_config_summary()
            }),
            status_code=500,
            headers={'Content-Type': 'application/json'}
        )

def main_timer(mytimer: func.TimerRequest) -> None:
    """
    Versão Timer Trigger para execução automática no dia configurado
    Configurar no function.json com expressão cron dinâmica baseada em AzureFunctionConfig.get_lock_check_cron()
    """
    logging.info('Timer trigger executado para verificação de lock da subscription')
    logging.info(f'Configuração atual: {AzureFunctionConfig.get_config_summary()}')
    
    # Simular HttpRequest para reutilizar a lógica
    fake_req = type('obj', (object,), {'params': {}})()
    
    try:
        response = main(fake_req)
        logging.info(f'Verificação automática concluída: {response.status_code}')
    except Exception as e:
        logging.error(f'Erro na verificação automática: {str(e)}')

