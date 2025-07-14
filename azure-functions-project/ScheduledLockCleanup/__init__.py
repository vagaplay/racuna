import azure.functions as func
import logging
import json
from datetime import datetime
from azure.identity import DefaultAzureCredential, ClientSecretCredential
from azure.mgmt.resource.locks import ManagementLockClient
import os

def main(req: func.HttpRequest) -> func.HttpResponse:
    """
    Azure Function para remoção agendada de lock da subscription
    
    EXECUTA: Todo dia 02 do mês
    FUNÇÃO: Remove lock da subscription (colocado pelo trigger de budget)
    MOTIVO: Limpeza mensal do lock de proteção
    """
    
    logging.info('=== REMOÇÃO AGENDADA DE LOCK DA SUBSCRIPTION (DIA 02) ===')
    
    try:
        # Verificar se hoje é dia 02
        today = datetime.utcnow()
        if today.day != 2:
            return func.HttpResponse(
                json.dumps({
                    'message': f'Função executada fora do dia agendado. Hoje: {today.day}/02',
                    'scheduled_day': 2,
                    'current_day': today.day,
                    'next_execution': f'02/{today.month + 1 if today.month < 12 else 1}/{today.year if today.month < 12 else today.year + 1}'
                }),
                status_code=200,
                headers={'Content-Type': 'application/json'}
            )
        
        # Configurações de autenticação
        subscription_id = os.environ.get('AZURE_SUBSCRIPTION_ID')
        tenant_id = os.environ.get('AZURE_TENANT_ID')
        client_id = os.environ.get('AZURE_CLIENT_ID')
        client_secret = os.environ.get('AZURE_CLIENT_SECRET')
        
        if not subscription_id:
            raise ValueError("AZURE_SUBSCRIPTION_ID não configurado")
        
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
        
        # Resultado da operação
        result = {
            'timestamp': datetime.utcnow().isoformat(),
            'execution_day': today.day,
            'subscription_id': subscription_id,
            'locks_found': [],
            'locks_removed': [],
            'errors': []
        }
        
        logging.info(f'Verificando locks na subscription: {subscription_id}')
        
        # Listar todos os locks da subscription
        subscription_locks = list(lock_client.management_locks.list_at_subscription_level())
        
        if not subscription_locks:
            result['message'] = 'Nenhum lock encontrado na subscription'
            logging.info('✅ Nenhum lock encontrado na subscription')
        else:
            logging.info(f'📋 Encontrados {len(subscription_locks)} locks na subscription')
            
            for lock in subscription_locks:
                lock_info = {
                    'name': lock.name,
                    'level': lock.level,
                    'notes': lock.notes or 'Sem notas',
                    'scope': lock.scope
                }
                result['locks_found'].append(lock_info)
                
                try:
                    # Verificar se é um lock de budget (baseado no nome ou notas)
                    is_budget_lock = (
                        'budget' in lock.name.lower() or
                        'budget' in (lock.notes or '').lower() or
                        'cost' in lock.name.lower() or
                        'limit' in lock.name.lower()
                    )
                    
                    if is_budget_lock:
                        logging.info(f'🔒 Removendo lock de budget: {lock.name}')
                        
                        # REMOVER O LOCK DA SUBSCRIPTION
                        lock_client.management_locks.delete_at_subscription_level(lock.name)
                        
                        lock_info['removed'] = True
                        lock_info['reason'] = 'Lock de budget removido na limpeza mensal'
                        result['locks_removed'].append(lock_info)
                        
                        logging.info(f'✅ Lock {lock.name} removido com sucesso')
                    else:
                        logging.info(f'⚠️ Lock {lock.name} mantido (não é lock de budget)')
                        lock_info['removed'] = False
                        lock_info['reason'] = 'Não é lock de budget - mantido'
                
                except Exception as e:
                    error_msg = f'Erro ao remover lock {lock.name}: {str(e)}'
                    logging.error(error_msg)
                    result['errors'].append({
                        'lock_name': lock.name,
                        'error': str(e)
                    })
        
        # Resumo final
        result['summary'] = {
            'total_locks_found': len(result['locks_found']),
            'locks_removed_count': len(result['locks_removed']),
            'errors_count': len(result['errors']),
            'execution_successful': len(result['errors']) == 0
        }
        
        # Log final
        if result['locks_removed']:
            logging.info(f'🎉 Limpeza concluída: {len(result["locks_removed"])} locks removidos')
        else:
            logging.info('✅ Limpeza concluída: Nenhum lock de budget encontrado')
        
        # Enviar notificação (se configurado)
        send_cleanup_notification(result)
        
        return func.HttpResponse(
            json.dumps(result, indent=2),
            status_code=200,
            headers={'Content-Type': 'application/json'}
        )
        
    except Exception as e:
        error_msg = f'Erro na remoção agendada de locks: {str(e)}'
        logging.error(error_msg)
        
        return func.HttpResponse(
            json.dumps({
                'error': error_msg,
                'timestamp': datetime.utcnow().isoformat(),
                'execution_day': datetime.utcnow().day
            }),
            status_code=500,
            headers={'Content-Type': 'application/json'}
        )

def send_cleanup_notification(result):
    """
    Envia notificação sobre a limpeza de locks realizada
    """
    try:
        if result['locks_removed']:
            message = f"""
🗓️ LIMPEZA MENSAL DE LOCKS - DIA 02

📊 Resumo:
• Locks encontrados: {result['summary']['total_locks_found']}
• Locks removidos: {result['summary']['locks_removed_count']}
• Erros: {result['summary']['errors_count']}

🔒 Locks removidos:
"""
            for lock in result['locks_removed']:
                message += f"• {lock['name']} ({lock['level']})\n"
            
            logging.info(f"📧 Notificação de limpeza: {message}")
            
            # Em produção, enviaria email/Teams/Slack
            # send_email_notification(message)
            # send_teams_notification(message)
        
    except Exception as e:
        logging.error(f"Erro ao enviar notificação: {str(e)}")

# Função para ser chamada via Timer Trigger
def main_timer(mytimer: func.TimerRequest) -> None:
    """
    Versão Timer Trigger para execução automática todo dia 02
    Configurar no function.json: "schedule": "0 0 8 2 * *" (8h da manhã do dia 02)
    """
    logging.info('Timer trigger executado para limpeza de locks')
    
    # Simular HttpRequest para reutilizar a lógica
    fake_req = type('obj', (object,), {'params': {}})()
    
    try:
        response = main(fake_req)
        logging.info(f'Limpeza automática concluída: {response.status_code}')
    except Exception as e:
        logging.error(f'Erro na limpeza automática: {str(e)}')

