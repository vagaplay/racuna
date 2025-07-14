import azure.functions as func
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)

# Criar app de functions
app = func.FunctionApp()

# ============================================================================
# FUNCTION 1: Limpeza Agendada de Locks (Todo dia 02)
# ============================================================================

@app.timer_trigger(schedule="0 0 8 2 * *", arg_name="mytimer", run_on_startup=False)
def scheduled_lock_cleanup_timer(mytimer: func.TimerRequest) -> None:
    """
    Timer Trigger: Executa todo dia 02 às 8h da manhã
    Função: Remove locks da subscription colocados pelo trigger de budget
    """
    from .ScheduledLockCleanup import main_timer
    main_timer(mytimer)

@app.route(route="scheduled-lock-cleanup", auth_level=func.AuthLevel.FUNCTION, methods=["GET", "POST"])
def scheduled_lock_cleanup_http(req: func.HttpRequest) -> func.HttpResponse:
    """
    HTTP Trigger: Para execução manual da limpeza de locks
    """
    from .ScheduledLockCleanup import main
    return main(req)

# ============================================================================
# FUNCTION 2: Remoção de Locks por Budget Excedido
# ============================================================================

@app.route(route="budget-exceeded-unlock", auth_level=func.AuthLevel.FUNCTION, methods=["POST"])
def budget_exceeded_unlock(req: func.HttpRequest) -> func.HttpResponse:
    """
    HTTP Trigger: Chamado quando budget é excedido
    Função: Remove locks de todos os recursos antes da exclusão
    """
    from .BudgetExceededUnlock import main
    return main(req)

# ============================================================================
# FUNCTION 3: Limpeza de Recursos Sem Tags (Melhorada)
# ============================================================================

@app.timer_trigger(schedule="0 0 2 * * *", arg_name="mytimer", run_on_startup=False)
def cleanup_untagged_resources_timer(mytimer: func.TimerRequest) -> None:
    """
    Timer Trigger: Executa diariamente às 2h da manhã
    Função: Identifica e remove recursos sem tags obrigatórias
    """
    from .CleanupUntaggedResources import main_timer
    main_timer(mytimer)

@app.route(route="cleanup-untagged-resources", auth_level=func.AuthLevel.FUNCTION, methods=["GET", "POST"])
def cleanup_untagged_resources_http(req: func.HttpRequest) -> func.HttpResponse:
    """
    HTTP Trigger: Para execução manual da limpeza de recursos
    """
    from .CleanupUntaggedResources import main
    return main(req)

# ============================================================================
# FUNCTION 4: Shutdown de Recursos Agendado
# ============================================================================

@app.timer_trigger(schedule="0 0 18 * * 1-5", arg_name="mytimer", run_on_startup=False)
def shutdown_scheduled_resources_timer(mytimer: func.TimerRequest) -> None:
    """
    Timer Trigger: Executa às 18h, segunda a sexta
    Função: Desliga VMs e outros recursos conforme agendamento
    """
    from .ShutdownScheduledResources import main_timer
    main_timer(mytimer)

@app.route(route="shutdown-scheduled-resources", auth_level=func.AuthLevel.FUNCTION, methods=["GET", "POST"])
def shutdown_scheduled_resources_http(req: func.HttpRequest) -> func.HttpResponse:
    """
    HTTP Trigger: Para execução manual do shutdown
    """
    from .ShutdownScheduledResources import main
    return main(req)

# ============================================================================
# FUNCTION 5: Monitoramento de Custos e Alertas
# ============================================================================

@app.timer_trigger(schedule="0 0 */6 * * *", arg_name="mytimer", run_on_startup=False)
def cost_monitoring_timer(mytimer: func.TimerRequest) -> None:
    """
    Timer Trigger: Executa a cada 6 horas
    Função: Monitora custos e envia alertas
    """
    from .CostMonitoring import main_timer
    main_timer(mytimer)

@app.route(route="cost-monitoring", auth_level=func.AuthLevel.FUNCTION, methods=["GET", "POST"])
def cost_monitoring_http(req: func.HttpRequest) -> func.HttpResponse:
    """
    HTTP Trigger: Para verificação manual de custos
    """
    from .CostMonitoring import main
    return main(req)

# ============================================================================
# FUNCTION 6: Webhook para Budget Alerts
# ============================================================================

@app.route(route="budget-webhook", auth_level=func.AuthLevel.ANONYMOUS, methods=["POST"])
def budget_webhook(req: func.HttpRequest) -> func.HttpResponse:
    """
    Webhook: Recebe alertas do Azure Budget
    Função: Processa alertas e aciona ações automáticas
    """
    try:
        import json
        
        # Log do webhook recebido
        logging.info("=== WEBHOOK BUDGET RECEBIDO ===")
        
        # Obter dados do webhook
        try:
            webhook_data = req.get_json()
        except:
            webhook_data = {}
        
        # Log dos dados recebidos
        logging.info(f"Dados do webhook: {json.dumps(webhook_data, indent=2)}")
        
        # Verificar se é alerta de budget excedido
        if webhook_data and 'data' in webhook_data:
            alert_data = webhook_data['data']
            
            # Extrair informações do alerta
            budget_name = alert_data.get('budgetName', 'Unknown')
            threshold = alert_data.get('threshold', 0)
            actual_spend = alert_data.get('actualSpend', 0)
            forecasted_spend = alert_data.get('forecastedSpend', 0)
            
            logging.info(f"Budget: {budget_name}, Threshold: {threshold}%, Actual: ${actual_spend}, Forecast: ${forecasted_spend}")
            
            # Se threshold >= 100%, acionar remoção de locks
            if threshold >= 100:
                logging.critical(f"🚨 BUDGET EXCEDIDO: {threshold}% - Acionando remoção de locks")
                
                # Chamar function de remoção de locks
                from .BudgetExceededUnlock import main as budget_unlock_main
                
                # Simular requisição para a function
                fake_req = type('obj', (object,), {
                    'params': {
                        'budget_limit': str(actual_spend / (threshold / 100)),
                        'current_cost': str(actual_spend),
                        'force_unlock': 'true'
                    }
                })()
                
                unlock_result = budget_unlock_main(fake_req)
                logging.info(f"Resultado da remoção de locks: {unlock_result.status_code}")
        
        return func.HttpResponse(
            json.dumps({
                'status': 'webhook_processed',
                'timestamp': func.datetime.utcnow().isoformat(),
                'data_received': webhook_data is not None
            }),
            status_code=200,
            headers={'Content-Type': 'application/json'}
        )
        
    except Exception as e:
        logging.error(f"Erro no webhook de budget: {str(e)}")
        return func.HttpResponse(
            json.dumps({'error': str(e)}),
            status_code=500,
            headers={'Content-Type': 'application/json'}
        )

# ============================================================================
# FUNCTION 7: Health Check
# ============================================================================

@app.route(route="health", auth_level=func.AuthLevel.ANONYMOUS, methods=["GET"])
def health_check(req: func.HttpRequest) -> func.HttpResponse:
    """
    Health Check: Verifica se as functions estão funcionando
    """
    import json
    from datetime import datetime
    
    health_status = {
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'functions': {
            'scheduled_lock_cleanup': 'active',
            'budget_exceeded_unlock': 'active',
            'cleanup_untagged_resources': 'active',
            'shutdown_scheduled_resources': 'active',
            'cost_monitoring': 'active',
            'budget_webhook': 'active'
        },
        'environment': {
            'subscription_id': 'configured' if func.os.environ.get('AZURE_SUBSCRIPTION_ID') else 'missing',
            'tenant_id': 'configured' if func.os.environ.get('AZURE_TENANT_ID') else 'missing',
            'client_id': 'configured' if func.os.environ.get('AZURE_CLIENT_ID') else 'missing',
            'client_secret': 'configured' if func.os.environ.get('AZURE_CLIENT_SECRET') else 'missing'
        }
    }
    
    return func.HttpResponse(
        json.dumps(health_status, indent=2),
        status_code=200,
        headers={'Content-Type': 'application/json'}
    )

