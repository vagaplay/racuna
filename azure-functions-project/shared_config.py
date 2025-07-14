"""
Configurações compartilhadas para Azure Functions
Permite customização de parâmetros via variáveis de ambiente
"""
import os
from datetime import datetime, time

class AzureFunctionConfig:
    """Configurações customizáveis para Azure Functions"""
    
    # Configurações de agendamento
    LOCK_CHECK_DAY = int(os.getenv('LOCK_CHECK_DAY', '2'))  # Dia do mês para verificar lock (padrão: dia 2)
    SHUTDOWN_HOUR = int(os.getenv('SHUTDOWN_HOUR', '19'))  # Hora para shutdown (padrão: 19h)
    TAG_CHECK_HOUR = int(os.getenv('TAG_CHECK_HOUR', '19'))  # Hora para verificar tags (padrão: 19h)
    
    # Configurações de budget
    BUDGET_START_DATE = os.getenv('BUDGET_START_DATE', datetime.now().strftime('%Y-%m-01'))
    BUDGET_END_DATE = os.getenv('BUDGET_END_DATE', datetime.now().strftime('%Y-12-31'))
    BUDGET_AMOUNT = float(os.getenv('BUDGET_AMOUNT', '200.0'))
    BUDGET_CURRENCY = os.getenv('BUDGET_CURRENCY', 'USD')
    
    # Configurações de Azure
    SUBSCRIPTION_ID = os.getenv('AZURE_SUBSCRIPTION_ID')
    TENANT_ID = os.getenv('AZURE_TENANT_ID')
    CLIENT_ID = os.getenv('AZURE_CLIENT_ID')
    CLIENT_SECRET = os.getenv('AZURE_CLIENT_SECRET')
    
    # Configurações de lock
    BUDGET_LOCK_NAME = os.getenv('BUDGET_LOCK_NAME', 'Prevent-Spending-BudgetControl')
    HOLD_LOCK_NAME = os.getenv('HOLD_LOCK_NAME', 'HoldLock')
    
    # Configurações de timezone
    TIMEZONE = os.getenv('TIMEZONE', 'America/Sao_Paulo')
    
    @classmethod
    def get_lock_check_cron(cls):
        """Retorna expressão cron para verificação de lock no dia configurado"""
        return f"0 0 8 {cls.LOCK_CHECK_DAY} * *"  # 8h da manhã no dia configurado
    
    @classmethod
    def get_shutdown_cron(cls):
        """Retorna expressão cron para shutdown de recursos"""
        return f"0 0 {cls.SHUTDOWN_HOUR} * * 1-5"  # Segunda a sexta no horário configurado
    
    @classmethod
    def get_tag_check_cron(cls):
        """Retorna expressão cron para verificação de tags"""
        return f"0 0 {cls.TAG_CHECK_HOUR} * * 1-5"  # Segunda a sexta no horário configurado
    
    @classmethod
    def validate_config(cls):
        """Valida se todas as configurações necessárias estão presentes"""
        required_vars = [
            'AZURE_SUBSCRIPTION_ID',
            'AZURE_TENANT_ID', 
            'AZURE_CLIENT_ID',
            'AZURE_CLIENT_SECRET'
        ]
        
        missing_vars = []
        for var in required_vars:
            if not getattr(cls, var.replace('AZURE_', '')):
                missing_vars.append(var)
        
        if missing_vars:
            raise ValueError(f"Variáveis de ambiente obrigatórias não configuradas: {', '.join(missing_vars)}")
        
        # Validar dia do mês
        if not 1 <= cls.LOCK_CHECK_DAY <= 31:
            raise ValueError(f"LOCK_CHECK_DAY deve estar entre 1 e 31, valor atual: {cls.LOCK_CHECK_DAY}")
        
        # Validar horas
        if not 0 <= cls.SHUTDOWN_HOUR <= 23:
            raise ValueError(f"SHUTDOWN_HOUR deve estar entre 0 e 23, valor atual: {cls.SHUTDOWN_HOUR}")
        
        if not 0 <= cls.TAG_CHECK_HOUR <= 23:
            raise ValueError(f"TAG_CHECK_HOUR deve estar entre 0 e 23, valor atual: {cls.TAG_CHECK_HOUR}")
        
        return True
    
    @classmethod
    def get_config_summary(cls):
        """Retorna resumo das configurações atuais"""
        return {
            "lock_check_day": cls.LOCK_CHECK_DAY,
            "shutdown_hour": cls.SHUTDOWN_HOUR,
            "tag_check_hour": cls.TAG_CHECK_HOUR,
            "budget_amount": cls.BUDGET_AMOUNT,
            "budget_currency": cls.BUDGET_CURRENCY,
            "budget_start_date": cls.BUDGET_START_DATE,
            "budget_end_date": cls.BUDGET_END_DATE,
            "timezone": cls.TIMEZONE,
            "lock_check_cron": cls.get_lock_check_cron(),
            "shutdown_cron": cls.get_shutdown_cron(),
            "tag_check_cron": cls.get_tag_check_cron()
        }

