"""
Rotas para configuração das Azure Functions
"""
from flask import Blueprint, request, jsonify, session
import json
import os
from datetime import datetime
from ..models.user import User

azure_functions_bp = Blueprint('azure_functions', __name__)

# Configurações padrão
DEFAULT_CONFIG = {
    'lock_check_day': 2,
    'shutdown_hour': 19,
    'tag_check_hour': 19,
    'budget_amount': 200.0,
    'budget_currency': 'USD',
    'budget_start_date': datetime.now().strftime('%Y-%m-01'),
    'budget_end_date': datetime.now().strftime('%Y-12-31'),
    'timezone': 'America/Sao_Paulo',
    'required_tags': 'Environment,Owner,Project'
}

@azure_functions_bp.route('/config', methods=['GET'])
def get_azure_functions_config():
    """Obter configurações atuais das Azure Functions"""
    try:
        # Verificar se usuário está logado
        if 'user_id' not in session:
            return jsonify({'error': 'Usuário não autenticado'}), 401
        
        user_id = session['user_id']
        user = User.get_by_id(user_id)
        
        if not user:
            return jsonify({'error': 'Usuário não encontrado'}), 404
        
        # Carregar configurações do usuário (se existir)
        config_file = f'/tmp/azure_functions_config_{user_id}.json'
        
        if os.path.exists(config_file):
            with open(config_file, 'r') as f:
                user_config = json.load(f)
        else:
            user_config = DEFAULT_CONFIG.copy()
        
        # Gerar expressões cron
        cron_expressions = {
            'lock_check_cron': f"0 0 8 {user_config['lock_check_day']} * *",
            'shutdown_cron': f"0 0 {user_config['shutdown_hour']} * * 1-5",
            'tag_check_cron': f"0 0 {user_config['tag_check_hour']} * * 1-5"
        }
        
        return jsonify({
            'config': user_config,
            'cron_expressions': cron_expressions,
            'last_updated': datetime.now().isoformat(),
            'user_id': user_id
        })
        
    except Exception as e:
        return jsonify({'error': f'Erro ao carregar configurações: {str(e)}'}), 500

@azure_functions_bp.route('/config', methods=['POST'])
def save_azure_functions_config():
    """Salvar configurações das Azure Functions"""
    try:
        # Verificar se usuário está logado
        if 'user_id' not in session:
            return jsonify({'error': 'Usuário não autenticado'}), 401
        
        user_id = session['user_id']
        user = User.get_by_id(user_id)
        
        if not user:
            return jsonify({'error': 'Usuário não encontrado'}), 404
        
        # Obter dados do request
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Dados não fornecidos'}), 400
        
        # Validar configurações
        config = {}
        
        # Validar dia de verificação de lock
        lock_check_day = data.get('lockCheckDay', DEFAULT_CONFIG['lock_check_day'])
        if not isinstance(lock_check_day, int) or not 1 <= lock_check_day <= 31:
            return jsonify({'error': 'Dia de verificação de lock deve estar entre 1 e 31'}), 400
        config['lock_check_day'] = lock_check_day
        
        # Validar horário de shutdown
        shutdown_hour = data.get('shutdownHour', DEFAULT_CONFIG['shutdown_hour'])
        if not isinstance(shutdown_hour, int) or not 0 <= shutdown_hour <= 23:
            return jsonify({'error': 'Horário de shutdown deve estar entre 0 e 23'}), 400
        config['shutdown_hour'] = shutdown_hour
        
        # Validar horário de verificação de tags
        tag_check_hour = data.get('tagCheckHour', DEFAULT_CONFIG['tag_check_hour'])
        if not isinstance(tag_check_hour, int) or not 0 <= tag_check_hour <= 23:
            return jsonify({'error': 'Horário de verificação de tags deve estar entre 0 e 23'}), 400
        config['tag_check_hour'] = tag_check_hour
        
        # Validar budget
        budget_amount = data.get('budgetAmount', DEFAULT_CONFIG['budget_amount'])
        if not isinstance(budget_amount, (int, float)) or budget_amount < 0:
            return jsonify({'error': 'Valor do budget deve ser um número positivo'}), 400
        config['budget_amount'] = float(budget_amount)
        
        # Validar moeda
        budget_currency = data.get('budgetCurrency', DEFAULT_CONFIG['budget_currency'])
        if budget_currency not in ['USD', 'BRL', 'EUR']:
            return jsonify({'error': 'Moeda deve ser USD, BRL ou EUR'}), 400
        config['budget_currency'] = budget_currency
        
        # Validar datas
        budget_start_date = data.get('budgetStartDate', DEFAULT_CONFIG['budget_start_date'])
        budget_end_date = data.get('budgetEndDate', DEFAULT_CONFIG['budget_end_date'])
        
        try:
            datetime.strptime(budget_start_date, '%Y-%m-%d')
            datetime.strptime(budget_end_date, '%Y-%m-%d')
        except ValueError:
            return jsonify({'error': 'Formato de data inválido (use YYYY-MM-DD)'}), 400
        
        config['budget_start_date'] = budget_start_date
        config['budget_end_date'] = budget_end_date
        
        # Validar timezone
        timezone = data.get('timezone', DEFAULT_CONFIG['timezone'])
        config['timezone'] = timezone
        
        # Validar tags obrigatórias
        required_tags = data.get('requiredTags', DEFAULT_CONFIG['required_tags'])
        if not required_tags or not isinstance(required_tags, str):
            return jsonify({'error': 'Tags obrigatórias devem ser fornecidas'}), 400
        config['required_tags'] = required_tags
        
        # Adicionar timestamp
        config['last_updated'] = datetime.now().isoformat()
        config['updated_by'] = user_id
        
        # Salvar configurações
        config_file = f'/tmp/azure_functions_config_{user_id}.json'
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
        
        # Gerar expressões cron
        cron_expressions = {
            'lock_check_cron': f"0 0 8 {config['lock_check_day']} * *",
            'shutdown_cron': f"0 0 {config['shutdown_hour']} * * 1-5",
            'tag_check_cron': f"0 0 {config['tag_check_hour']} * * 1-5"
        }
        
        return jsonify({
            'message': 'Configurações salvas com sucesso',
            'config': config,
            'cron_expressions': cron_expressions,
            'user_id': user_id
        })
        
    except Exception as e:
        return jsonify({'error': f'Erro ao salvar configurações: {str(e)}'}), 500

@azure_functions_bp.route('/test/<function_name>', methods=['POST'])
def test_azure_function(function_name):
    """Testar execução de uma Azure Function específica"""
    try:
        # Verificar se usuário está logado
        if 'user_id' not in session:
            return jsonify({'error': 'Usuário não autenticado'}), 401
        
        user_id = session['user_id']
        
        # Funções disponíveis para teste
        available_functions = {
            'lock-check': 'Verificação de Lock da Subscription',
            'cleanup-resources': 'Limpeza de Recursos sem Tags',
            'budget-exceeded': 'Remoção de Locks por Budget Excedido'
        }
        
        if function_name not in available_functions:
            return jsonify({'error': f'Função {function_name} não encontrada'}), 404
        
        # Carregar configurações do usuário
        config_file = f'/tmp/azure_functions_config_{user_id}.json'
        
        if os.path.exists(config_file):
            with open(config_file, 'r') as f:
                user_config = json.load(f)
        else:
            user_config = DEFAULT_CONFIG.copy()
        
        # Simular execução da função (em produção, chamaria a Azure Function real)
        test_result = {
            'function_name': function_name,
            'function_description': available_functions[function_name],
            'test_timestamp': datetime.now().isoformat(),
            'config_used': user_config,
            'status': 'success',
            'message': f'Teste da função {available_functions[function_name]} executado com sucesso',
            'simulated': True,
            'note': 'Este é um teste simulado. Em produção, executaria a Azure Function real.'
        }
        
        # Adicionar detalhes específicos por função
        if function_name == 'lock-check':
            test_result['details'] = {
                'scheduled_day': user_config['lock_check_day'],
                'next_execution': f"Dia {user_config['lock_check_day']} às 8h",
                'target_lock': 'Prevent-Spending-BudgetControl'
            }
        elif function_name == 'cleanup-resources':
            test_result['details'] = {
                'scheduled_hour': user_config['tag_check_hour'],
                'required_tags': user_config['required_tags'].split(','),
                'execution_days': 'Segunda a Sexta'
            }
        elif function_name == 'budget-exceeded':
            test_result['details'] = {
                'budget_amount': user_config['budget_amount'],
                'budget_currency': user_config['budget_currency'],
                'trigger': 'Quando budget excede 100% do limite'
            }
        
        return jsonify(test_result)
        
    except Exception as e:
        return jsonify({'error': f'Erro no teste da função: {str(e)}'}), 500

@azure_functions_bp.route('/status', methods=['GET'])
def get_azure_functions_status():
    """Obter status das Azure Functions"""
    try:
        # Verificar se usuário está logado
        if 'user_id' not in session:
            return jsonify({'error': 'Usuário não autenticado'}), 401
        
        user_id = session['user_id']
        
        # Em produção, verificaria o status real das Azure Functions
        # Por enquanto, retorna status simulado
        status = {
            'timestamp': datetime.now().isoformat(),
            'functions': {
                'lock-check': {
                    'name': 'Verificação de Lock',
                    'status': 'active',
                    'last_execution': '2024-01-02T08:00:00Z',
                    'next_execution': '2024-02-02T08:00:00Z',
                    'success_rate': '100%'
                },
                'cleanup-resources': {
                    'name': 'Limpeza de Recursos',
                    'status': 'active',
                    'last_execution': '2024-01-15T19:00:00Z',
                    'next_execution': '2024-01-16T19:00:00Z',
                    'success_rate': '95%'
                },
                'budget-exceeded': {
                    'name': 'Budget Excedido',
                    'status': 'standby',
                    'last_execution': 'Never',
                    'next_execution': 'On budget threshold',
                    'success_rate': 'N/A'
                }
            },
            'overall_status': 'healthy',
            'note': 'Status simulado - Em produção, conectaria com Azure Functions reais'
        }
        
        return jsonify(status)
        
    except Exception as e:
        return jsonify({'error': f'Erro ao obter status: {str(e)}'}), 500

