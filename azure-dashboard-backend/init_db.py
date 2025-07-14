#!/usr/bin/env python3
"""
Script para inicializar o banco de dados com todas as tabelas
"""

import os
import sys

# Adicionar o diretório pai ao path para importar os módulos
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from src.models.user import db, User
from src.models.subscription import Subscription
from src.models.budget_config import BudgetConfig
from src.models.deployment import Deployment
from src.models.scheduled_task import ScheduledTask
from src.models.system_setting import SystemSetting
from src.models.azure_credentials import AzureCredentials
from src.main import app

def init_database():
    """Inicializa o banco de dados com todas as tabelas"""
    with app.app_context():
        # Criar diretório do banco se não existir
        db_dir = os.path.dirname(app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', ''))
        if not os.path.exists(db_dir):
            os.makedirs(db_dir)
        
        # Criar todas as tabelas
        db.create_all()
        
        print("✅ Banco de dados inicializado com sucesso!")
        print("📋 Tabelas criadas:")
        print("   - users")
        print("   - subscriptions")
        print("   - budget_configs")
        print("   - deployments")
        print("   - scheduled_tasks")
        print("   - system_settings")
        print("   - azure_credentials")
        
        # Verificar se existem usuários
        user_count = User.query.count()
        print(f"👥 Usuários existentes: {user_count}")
        
        if user_count == 0:
            print("💡 Dica: Crie uma conta através da interface web para começar a usar o sistema")

if __name__ == "__main__":
    init_database()

