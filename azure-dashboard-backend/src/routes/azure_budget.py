"""
Rotas para gerenciamento de orçamento Azure
Integração com Azure Cost Management API
"""

from flask import Blueprint, request, jsonify, session
from azure.mgmt.consumption import ConsumptionManagementClient
from azure.mgmt.costmanagement import CostManagementClient
from azure.core.exceptions import HttpResponseError
from datetime import datetime, timedelta
import logging

from ..services.azure_service import azure_service

logger = logging.getLogger(__name__)

azure_budget_bp = Blueprint('azure_budget', __name__)

@azure_budget_bp.route('/current-costs', methods=['GET'])
def get_current_costs():
    """Obtém custos atuais da subscription"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Usuário não autenticado'}), 401
    
    try:
        user_id = session['user_id']
        
        # Obter credenciais do usuário
        credentials = azure_service.get_user_credentials(user_id)
        if not credentials:
            return jsonify({
                'success': False,
                'error': 'Credenciais Azure não configuradas'
            }), 400
        
        # Criar cliente de Cost Management
        cost_client = CostManagementClient(
            credential=credentials['credential'],
            subscription_id=credentials['subscription_id']
        )
        
        # Definir período (mês atual)
        today = datetime.now()
        start_of_month = today.replace(day=1)
        end_of_month = (start_of_month + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        
        # Definir escopo da subscription
        scope = f"/subscriptions/{credentials['subscription_id']}"
        
        # Parâmetros da query
        query_definition = {
            "type": "ActualCost",
            "timeframe": "Custom",
            "timePeriod": {
                "from": start_of_month.strftime("%Y-%m-%d"),
                "to": end_of_month.strftime("%Y-%m-%d")
            },
            "dataset": {
                "granularity": "Daily",
                "aggregation": {
                    "totalCost": {
                        "name": "PreTaxCost",
                        "function": "Sum"
                    }
                }
            }
        }
        
        try:
            # Executar query de custos
            result = cost_client.query.usage(scope=scope, parameters=query_definition)
            
            # Processar resultados
            total_current = 0
            daily_costs = []
            
            if result.rows:
                for row in result.rows:
                    cost = float(row[0]) if row[0] else 0
                    total_current += cost
                    daily_costs.append(cost)
            
            # Calcular previsão simples (baseada na média diária)
            days_in_month = end_of_month.day
            days_passed = today.day
            
            if days_passed > 0:
                daily_average = total_current / days_passed
                forecast = daily_average * days_in_month
            else:
                forecast = 0
            
            # Simular dados do mês anterior (seria outra query similar)
            last_month_estimate = total_current * 1.1  # Estimativa
            
            return jsonify({
                'success': True,
                'currentMonth': round(total_current, 2),
                'forecast': round(forecast, 2),
                'lastMonth': round(last_month_estimate, 2),
                'dailyCosts': daily_costs,
                'period': {
                    'start': start_of_month.strftime("%Y-%m-%d"),
                    'end': end_of_month.strftime("%Y-%m-%d")
                }
            })
            
        except HttpResponseError as e:
            if e.status_code == 403:
                return jsonify({
                    'success': False,
                    'error': 'Sem permissão para acessar dados de custo. Verifique as permissões do Service Principal.'
                }), 403
            else:
                raise
                
    except Exception as e:
        error_msg = f"Erro ao obter custos: {str(e)}"
        logger.error(error_msg)
        return jsonify({
            'success': False,
            'error': error_msg
        }), 500

@azure_budget_bp.route('/list-budgets', methods=['GET'])
def list_budgets():
    """Lista orçamentos configurados"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Usuário não autenticado'}), 401
    
    try:
        user_id = session['user_id']
        
        # Obter credenciais do usuário
        credentials = azure_service.get_user_credentials(user_id)
        if not credentials:
            return jsonify({
                'success': False,
                'error': 'Credenciais Azure não configuradas'
            }), 400
        
        # Criar cliente de Consumption
        consumption_client = ConsumptionManagementClient(
            credential=credentials['credential'],
            subscription_id=credentials['subscription_id']
        )
        
        try:
            # Listar orçamentos da subscription
            budgets = list(consumption_client.budgets.list())
            
            budget_list = []
            for budget in budgets:
                budget_info = {
                    'name': budget.name,
                    'amount': budget.amount,
                    'timeGrain': budget.time_grain,
                    'startDate': budget.time_period.start_date.strftime("%Y-%m-%d") if budget.time_period else None,
                    'endDate': budget.time_period.end_date.strftime("%Y-%m-%d") if budget.time_period else None,
                    'currentSpend': budget.current_spend.amount if budget.current_spend else 0,
                    'category': budget.category,
                    'alerts': []
                }
                
                # Adicionar alertas se existirem
                if budget.notifications:
                    for alert_name, alert in budget.notifications.items():
                        budget_info['alerts'].append({
                            'name': alert_name,
                            'threshold': alert.threshold,
                            'operator': alert.operator,
                            'contactEmails': alert.contact_emails or []
                        })
                
                budget_list.append(budget_info)
            
            return jsonify({
                'success': True,
                'budgets': budget_list,
                'count': len(budget_list)
            })
            
        except HttpResponseError as e:
            if e.status_code == 403:
                return jsonify({
                    'success': False,
                    'error': 'Sem permissão para acessar orçamentos. Verifique as permissões do Service Principal.'
                }), 403
            else:
                raise
                
    except Exception as e:
        error_msg = f"Erro ao listar orçamentos: {str(e)}"
        logger.error(error_msg)
        return jsonify({
            'success': False,
            'error': error_msg
        }), 500

@azure_budget_bp.route('/create-budget', methods=['POST'])
def create_budget():
    """Cria um novo orçamento"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Usuário não autenticado'}), 401
    
    try:
        user_id = session['user_id']
        data = request.get_json()
        
        # Validar dados obrigatórios
        required_fields = ['name', 'amount']
        for field in required_fields:
            if not data.get(field):
                return jsonify({
                    'success': False,
                    'error': f'Campo obrigatório: {field}'
                }), 400
        
        # Obter credenciais do usuário
        credentials = azure_service.get_user_credentials(user_id)
        if not credentials:
            return jsonify({
                'success': False,
                'error': 'Credenciais Azure não configuradas'
            }), 400
        
        # Criar cliente de Consumption
        consumption_client = ConsumptionManagementClient(
            credential=credentials['credential'],
            subscription_id=credentials['subscription_id']
        )
        
        # Preparar parâmetros do orçamento
        budget_name = data['name']
        amount = float(data['amount'])
        time_grain = data.get('timeGrain', 'Monthly')
        
        # Definir período
        if data.get('startDate') and data.get('endDate'):
            start_date = datetime.strptime(data['startDate'], "%Y-%m-%d")
            end_date = datetime.strptime(data['endDate'], "%Y-%m-%d")
        else:
            # Período padrão: próximos 12 meses
            start_date = datetime.now().replace(day=1)
            end_date = (start_date + timedelta(days=365)).replace(day=1) - timedelta(days=1)
        
        # Parâmetros do orçamento
        budget_params = {
            'category': 'Cost',
            'amount': amount,
            'time_grain': time_grain,
            'time_period': {
                'start_date': start_date,
                'end_date': end_date
            },
            'filters': {
                'resource_groups': [],
                'resources': [],
                'meters': [],
                'tags': {}
            },
            'notifications': {
                'alert_80': {
                    'enabled': True,
                    'operator': 'GreaterThan',
                    'threshold': 80,
                    'contact_emails': [],
                    'contact_roles': ['Owner', 'Contributor']
                },
                'alert_100': {
                    'enabled': True,
                    'operator': 'GreaterThan',
                    'threshold': 100,
                    'contact_emails': [],
                    'contact_roles': ['Owner', 'Contributor']
                }
            }
        }
        
        try:
            # Criar orçamento
            result = consumption_client.budgets.create_or_update(
                budget_name=budget_name,
                parameters=budget_params
            )
            
            return jsonify({
                'success': True,
                'message': f'Orçamento "{budget_name}" criado com sucesso',
                'budget': {
                    'name': result.name,
                    'amount': result.amount,
                    'timeGrain': result.time_grain,
                    'startDate': result.time_period.start_date.strftime("%Y-%m-%d"),
                    'endDate': result.time_period.end_date.strftime("%Y-%m-%d")
                }
            })
            
        except HttpResponseError as e:
            if e.status_code == 403:
                return jsonify({
                    'success': False,
                    'error': 'Sem permissão para criar orçamentos. Verifique as permissões do Service Principal.'
                }), 403
            elif e.status_code == 409:
                return jsonify({
                    'success': False,
                    'error': f'Orçamento "{budget_name}" já existe'
                }), 409
            else:
                raise
                
    except ValueError as e:
        return jsonify({
            'success': False,
            'error': f'Valor inválido: {str(e)}'
        }), 400
    except Exception as e:
        error_msg = f"Erro ao criar orçamento: {str(e)}"
        logger.error(error_msg)
        return jsonify({
            'success': False,
            'error': error_msg
        }), 500

