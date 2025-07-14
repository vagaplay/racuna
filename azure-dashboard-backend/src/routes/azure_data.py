"""
Rotas para obtenção de dados Azure (custos, recursos, etc.)
"""

from flask import Blueprint, request, jsonify, session
from src.services.azure_service import azure_auth_service, azure_resource_service, azure_cost_service
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

azure_data_bp = Blueprint('azure_data', __name__)

@azure_data_bp.route('/dashboard/summary', methods=['GET'])
def get_dashboard_summary():
    """
    Obtém resumo do dashboard com dados principais
    """
    try:
        if 'user_id' not in session:
            return jsonify({'error': 'Usuário não autenticado'}), 401
        
        user_id = session['user_id']
        
        if not azure_auth_service.is_user_authenticated(user_id):
            return jsonify({'error': 'Credenciais Azure não configuradas'}), 400
        
        # Obter dados de resource groups
        rg_result = azure_resource_service.list_resource_groups(user_id)
        if 'error' in rg_result:
            return jsonify({'error': f'Erro ao obter resource groups: {rg_result["error"]}'}), 400
        
        # Obter dados de recursos
        resources_result = azure_resource_service.list_resources(user_id)
        if 'error' in resources_result:
            return jsonify({'error': f'Erro ao obter recursos: {resources_result["error"]}'}), 400
        
        # Obter custos do mês atual
        costs_result = azure_cost_service.get_current_month_costs(user_id)
        if 'error' in costs_result:
            return jsonify({'error': f'Erro ao obter custos: {costs_result["error"]}'}), 400
        
        # Processar top 5 serviços por custo
        service_costs = costs_result.get('service_costs', {})
        top_services = sorted(service_costs.items(), key=lambda x: x[1], reverse=True)[:5]
        
        return jsonify({
            'success': True,
            'data': {
                'current_month_cost': costs_result.get('total_cost', 0),
                'resource_groups_count': rg_result.get('count', 0),
                'resources_count': resources_result.get('count', 0),
                'top_services': top_services,
                'last_updated': datetime.utcnow().isoformat()
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Erro ao obter resumo do dashboard: {str(e)}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

@azure_data_bp.route('/costs/current', methods=['GET'])
def get_current_costs():
    """
    Obtém custos atuais detalhados
    """
    try:
        if 'user_id' not in session:
            return jsonify({'error': 'Usuário não autenticado'}), 401
        
        user_id = session['user_id']
        
        if not azure_auth_service.is_user_authenticated(user_id):
            return jsonify({'error': 'Credenciais Azure não configuradas'}), 400
        
        # Obter custos do mês atual
        result = azure_cost_service.get_current_month_costs(user_id)
        
        if 'error' in result:
            return jsonify({'error': result['error']}), 400
        
        return jsonify({
            'success': True,
            'data': result
        }), 200
        
    except Exception as e:
        logger.error(f"Erro ao obter custos atuais: {str(e)}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

@azure_data_bp.route('/costs/forecast', methods=['GET'])
def get_cost_forecast():
    """
    Obtém forecast de custos
    """
    try:
        if 'user_id' not in session:
            return jsonify({'error': 'Usuário não autenticado'}), 401
        
        user_id = session['user_id']
        
        if not azure_auth_service.is_user_authenticated(user_id):
            return jsonify({'error': 'Credenciais Azure não configuradas'}), 400
        
        # Por enquanto, vamos simular forecast baseado nos custos atuais
        # TODO: Implementar forecast real usando Azure Cost Management API
        
        # Obter custos atuais para base do forecast
        current_costs = azure_cost_service.get_current_month_costs(user_id)
        
        if 'error' in current_costs:
            return jsonify({'error': current_costs['error']}), 400
        
        # Simular forecast baseado na média dos custos atuais
        daily_costs = current_costs.get('daily_costs', [])
        if not daily_costs:
            return jsonify({
                'success': True,
                'data': {
                    'total_forecast': 0,
                    'daily_forecast': [],
                    'currency': 'USD'
                }
            }), 200
        
        # Calcular média diária
        total_cost = sum(item['cost'] for item in daily_costs)
        avg_daily_cost = total_cost / len(daily_costs) if daily_costs else 0
        
        # Gerar forecast para próximos dias
        days = int(request.args.get('days', 14))
        forecast_data = []
        
        for i in range(1, days + 1):
            date = datetime.now() + timedelta(days=i)
            # Adicionar variação de ±20% para simular incerteza
            import random
            variation = random.uniform(0.8, 1.2)
            forecast_cost = avg_daily_cost * variation
            
            forecast_data.append({
                'date': date.strftime('%Y-%m-%d'),
                'forecast_cost': round(forecast_cost, 2)
            })
        
        total_forecast = sum(item['forecast_cost'] for item in forecast_data)
        
        return jsonify({
            'success': True,
            'data': {
                'total_forecast': round(total_forecast, 2),
                'daily_forecast': forecast_data,
                'currency': 'USD',
                'based_on_days': len(daily_costs)
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Erro ao obter forecast: {str(e)}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

@azure_data_bp.route('/resources', methods=['GET'])
def get_resources():
    """
    Lista recursos da subscription
    """
    try:
        if 'user_id' not in session:
            return jsonify({'error': 'Usuário não autenticado'}), 401
        
        user_id = session['user_id']
        
        if not azure_auth_service.is_user_authenticated(user_id):
            return jsonify({'error': 'Credenciais Azure não configuradas'}), 400
        
        resource_group = request.args.get('resource_group')
        result = azure_resource_service.list_resources(user_id, resource_group)
        
        if 'error' in result:
            return jsonify({'error': result['error']}), 400
        
        return jsonify({
            'success': True,
            'data': result
        }), 200
        
    except Exception as e:
        logger.error(f"Erro ao listar recursos: {str(e)}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

@azure_data_bp.route('/resource-groups', methods=['GET'])
def get_resource_groups():
    """
    Lista resource groups da subscription
    """
    try:
        if 'user_id' not in session:
            return jsonify({'error': 'Usuário não autenticado'}), 401
        
        user_id = session['user_id']
        
        if not azure_auth_service.is_user_authenticated(user_id):
            return jsonify({'error': 'Credenciais Azure não configuradas'}), 400
        
        result = azure_resource_service.list_resource_groups(user_id)
        
        if 'error' in result:
            return jsonify({'error': result['error']}), 400
        
        return jsonify({
            'success': True,
            'data': result
        }), 200
        
    except Exception as e:
        logger.error(f"Erro ao listar resource groups: {str(e)}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

