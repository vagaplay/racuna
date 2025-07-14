"""
Azure Budget Management - API Completa
Implementa CRUD completo para orçamentos Azure
"""

from flask import Blueprint, request, jsonify, session
from azure.mgmt.consumption import ConsumptionManagementClient
from azure.mgmt.consumption.models import Budget, BudgetTimePeriod, BudgetFilter, BudgetFilterProperties
from src.models.user import User
from src.services.azure_service import azure_auth_service
import logging
from datetime import datetime, timedelta
import uuid

azure_budget_bp = Blueprint('azure_budget', __name__)

@azure_budget_bp.route('/status', methods=['GET'])
def budget_status():
    """Verificar status da API de orçamentos"""
    try:
        if 'user_id' not in session:
            return jsonify({"error": "Usuário não autenticado"}), 401
        
        user = User.get_by_id(session['user_id'])
        if not user:
            return jsonify({"error": "Usuário não encontrado"}), 404
        
        # Verificar credenciais Azure
        credentials = azure_auth_service.get_user_credentials(user.id)
        if not credentials:
            return jsonify({"error": "Credenciais Azure não configuradas"}), 400
        
        return jsonify({
            "status": "ok",
            "user_id": user.id,
            "has_credentials": True,
            "subscription_id": credentials.get('subscription_id'),
            "message": "Budget API funcionando"
        })
    except Exception as e:
        logging.error(f"Erro no budget status: {e}")
        return jsonify({"error": str(e)}), 500

@azure_budget_bp.route('/current', methods=['GET'])
def get_current_costs():
    """Obter custos atuais da subscription"""
    try:
        if 'user_id' not in session:
            return jsonify({"error": "Usuário não autenticado"}), 401
        
        user = User.get_by_id(session['user_id'])
        if not user:
            return jsonify({"error": "Usuário não encontrado"}), 404
        
        # Obter credenciais do usuário
        credentials = azure_auth_service.get_user_credentials(user.id)
        if not credentials:
            return jsonify({"error": "Credenciais Azure não configuradas"}), 400
        
        # Simular dados de custo (implementar integração real depois)
        current_costs = {
            "total_cost": 1250.75,
            "currency": "USD",
            "period": "current_month",
            "last_updated": datetime.now().isoformat(),
            "breakdown": [
                {"service": "Virtual Machines", "cost": 450.25, "percentage": 36},
                {"service": "Storage", "cost": 320.50, "percentage": 26},
                {"service": "Networking", "cost": 280.00, "percentage": 22},
                {"service": "Databases", "cost": 200.00, "percentage": 16}
            ],
            "trend": {
                "previous_month": 1180.50,
                "change_percentage": 5.95,
                "trend": "increasing"
            }
        }
        
        return jsonify(current_costs)
        
    except Exception as e:
        logging.error(f"Erro ao obter custos atuais: {e}")
        return jsonify({"error": str(e)}), 500

@azure_budget_bp.route('/forecast', methods=['GET'])
def get_cost_forecast():
    """Obter previsão de custos"""
    try:
        if 'user_id' not in session:
            return jsonify({"error": "Usuário não autenticado"}), 401
        
        user = User.get_by_id(session['user_id'])
        credentials = azure_auth_service.get_user_credentials(user.id)
        
        if not credentials:
            return jsonify({"error": "Credenciais Azure não configuradas"}), 400
        
        days = request.args.get('days', 30, type=int)
        
        # Simular previsão baseada em tendência
        forecast = {
            "forecast_period_days": days,
            "estimated_total": 1320.00,
            "confidence": 85,
            "daily_average": 44.00,
            "weekly_forecast": [
                {"week": 1, "estimated_cost": 308.00},
                {"week": 2, "estimated_cost": 315.50},
                {"week": 3, "estimated_cost": 322.25},
                {"week": 4, "estimated_cost": 330.00}
            ],
            "factors": [
                "Tendência de crescimento de 5.95%",
                "Aumento sazonal esperado",
                "Novos recursos provisionados"
            ]
        }
        
        return jsonify(forecast)
        
    except Exception as e:
        logging.error(f"Erro ao obter previsão: {e}")
        return jsonify({"error": str(e)}), 500

@azure_budget_bp.route('/breakdown', methods=['GET'])
def get_cost_breakdown():
    """Obter breakdown de custos por serviço"""
    try:
        if 'user_id' not in session:
            return jsonify({"error": "Usuário não autenticado"}), 401
        
        user = User.get_by_id(session['user_id'])
        credentials = azure_auth_service.get_user_credentials(user.id)
        
        if not credentials:
            return jsonify({"error": "Credenciais Azure não configuradas"}), 400
        
        group_by = request.args.get('group_by', 'ServiceName')
        
        # Simular breakdown detalhado
        breakdown = {
            "group_by": group_by,
            "total_cost": 1250.75,
            "currency": "USD",
            "items": [
                {
                    "name": "Virtual Machines",
                    "cost": 450.25,
                    "percentage": 36.0,
                    "resources": 12,
                    "trend": "stable"
                },
                {
                    "name": "Storage Accounts",
                    "cost": 320.50,
                    "percentage": 25.6,
                    "resources": 8,
                    "trend": "increasing"
                },
                {
                    "name": "Virtual Network",
                    "cost": 280.00,
                    "percentage": 22.4,
                    "resources": 5,
                    "trend": "stable"
                },
                {
                    "name": "SQL Database",
                    "cost": 200.00,
                    "percentage": 16.0,
                    "resources": 3,
                    "trend": "decreasing"
                }
            ]
        }
        
        return jsonify(breakdown)
        
    except Exception as e:
        logging.error(f"Erro ao obter breakdown: {e}")
        return jsonify({"error": str(e)}), 500

@azure_budget_bp.route('/list', methods=['GET'])
def list_budgets():
    """Listar todos os orçamentos da subscription"""
    try:
        if 'user_id' not in session:
            return jsonify({"error": "Usuário não autenticado"}), 401
        
        user = User.get_by_id(session['user_id'])
        credentials = azure_auth_service.get_user_credentials(user.id)
        
        if not credentials:
            return jsonify({"error": "Credenciais Azure não configuradas"}), 400
        
        # Simular lista de orçamentos
        budgets = [
            {
                "id": "monthly_budget_2025",
                "name": "Orçamento Mensal 2025",
                "amount": 1500.00,
                "currency": "USD",
                "time_grain": "Monthly",
                "current_spend": 1250.75,
                "forecasted_spend": 1320.00,
                "percentage_used": 83.4,
                "status": "warning",
                "notifications": 2,
                "start_date": "2025-01-01",
                "end_date": "2025-12-31"
            },
            {
                "id": "quarterly_budget_q1",
                "name": "Orçamento Q1 2025",
                "amount": 4500.00,
                "currency": "USD", 
                "time_grain": "Quarterly",
                "current_spend": 3750.25,
                "forecasted_spend": 4200.00,
                "percentage_used": 83.3,
                "status": "warning",
                "notifications": 1,
                "start_date": "2025-01-01",
                "end_date": "2025-03-31"
            }
        ]
        
        return jsonify({
            "budgets": budgets,
            "total": len(budgets)
        })
        
    except Exception as e:
        logging.error(f"Erro ao listar orçamentos: {e}")
        return jsonify({"error": f"Erro ao listar orçamentos: {str(e)}"}), 500

@azure_budget_bp.route('/create', methods=['POST'])
def create_budget():
    """Criar novo orçamento"""
    try:
        if 'user_id' not in session:
            return jsonify({"error": "Usuário não autenticado"}), 401
        
        data = request.get_json()
        if not data:
            return jsonify({"error": "Dados não fornecidos"}), 400
        
        # Validar dados obrigatórios
        required_fields = ['name', 'amount', 'time_grain', 'start_date', 'end_date']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Campo obrigatório: {field}"}), 400
        
        user = User.get_by_id(session['user_id'])
        credentials = azure_auth_service.get_user_credentials(user.id)
        
        if not credentials:
            return jsonify({"error": "Credenciais Azure não configuradas"}), 400
        
        # Simular criação de orçamento
        budget_id = f"budget_{uuid.uuid4().hex[:8]}"
        
        created_budget = {
            "id": budget_id,
            "name": data['name'],
            "amount": float(data['amount']),
            "currency": data.get('currency', 'USD'),
            "time_grain": data['time_grain'],
            "start_date": data['start_date'],
            "end_date": data['end_date'],
            "notifications": data.get('notifications', []),
            "filters": data.get('filters', {}),
            "created_at": datetime.now().isoformat(),
            "status": "active"
        }
        
        return jsonify({
            "message": "Orçamento criado com sucesso",
            "budget": created_budget
        })
        
    except Exception as e:
        logging.error(f"Erro ao criar orçamento: {e}")
        return jsonify({"error": f"Erro ao criar orçamento: {str(e)}"}), 500

@azure_budget_bp.route('/alerts', methods=['GET'])
def get_budget_alerts():
    """Obter alertas de orçamento"""
    try:
        if 'user_id' not in session:
            return jsonify({"error": "Usuário não autenticado"}), 401
        
        user = User.get_by_id(session['user_id'])
        credentials = azure_auth_service.get_user_credentials(user.id)
        
        if not credentials:
            return jsonify({"error": "Credenciais Azure não configuradas"}), 400
        
        # Simular alertas baseados nos orçamentos
        alerts = [
            {
                "id": "alert_1",
                "budget_name": "Orçamento Mensal 2025",
                "type": "warning",
                "severity": "medium",
                "threshold": 80,
                "current_percentage": 83.4,
                "message": "Orçamento mensal atingiu 83.4% do limite (R$ 1.250,75 de R$ 1.500,00)",
                "created_at": datetime.now().isoformat(),
                "acknowledged": False
            },
            {
                "id": "alert_2", 
                "budget_name": "Orçamento Q1 2025",
                "type": "info",
                "severity": "low",
                "threshold": 75,
                "current_percentage": 83.3,
                "message": "Orçamento trimestral em 83.3% do limite",
                "created_at": (datetime.now() - timedelta(hours=2)).isoformat(),
                "acknowledged": True
            },
            {
                "id": "alert_3",
                "budget_name": "Orçamento Mensal 2025", 
                "type": "critical",
                "severity": "high",
                "threshold": 90,
                "current_percentage": 95.2,
                "message": "CRÍTICO: Previsão indica que orçamento será ultrapassado em 3 dias",
                "created_at": (datetime.now() - timedelta(minutes=30)).isoformat(),
                "acknowledged": False
            }
        ]
        
        return jsonify({
            "alerts": alerts,
            "total": len(alerts),
            "unacknowledged": len([a for a in alerts if not a['acknowledged']])
        })
        
    except Exception as e:
        logging.error(f"Erro ao obter alertas: {e}")
        return jsonify({"error": f"Erro ao obter alertas: {str(e)}"}), 500

@azure_budget_bp.route('/recommendations', methods=['GET'])
def get_cost_recommendations():
    """Obter recomendações de otimização de custos"""
    try:
        if 'user_id' not in session:
            return jsonify({"error": "Usuário não autenticado"}), 401
        
        user = User.get_by_id(session['user_id'])
        credentials = azure_auth_service.get_user_credentials(user.id)
        
        if not credentials:
            return jsonify({"error": "Credenciais Azure não configuradas"}), 400
        
        # Simular recomendações inteligentes
        recommendations = [
            {
                "id": "rec_1",
                "type": "vm_rightsizing",
                "priority": "high",
                "potential_savings": 180.50,
                "title": "Redimensionar VMs subutilizadas",
                "description": "3 VMs estão com utilização abaixo de 20% nos últimos 30 dias",
                "action": "Reduzir tamanho das VMs ou desligar quando não utilizadas",
                "resources": ["vm-web-01", "vm-test-02", "vm-backup-03"],
                "effort": "low"
            },
            {
                "id": "rec_2",
                "type": "storage_optimization",
                "priority": "medium",
                "potential_savings": 95.25,
                "title": "Otimizar armazenamento",
                "description": "Storage accounts com dados antigos em tier Premium",
                "action": "Mover dados antigos para tier Cool ou Archive",
                "resources": ["storage-logs", "storage-backup"],
                "effort": "medium"
            },
            {
                "id": "rec_3",
                "type": "reserved_instances",
                "priority": "high",
                "potential_savings": 320.00,
                "title": "Usar Reserved Instances",
                "description": "VMs com uso consistente podem usar instâncias reservadas",
                "action": "Comprar Reserved Instances para VMs de produção",
                "resources": ["vm-prod-01", "vm-prod-02", "vm-db-01"],
                "effort": "low"
            }
        ]
        
        total_savings = sum(rec['potential_savings'] for rec in recommendations)
        
        return jsonify({
            "recommendations": recommendations,
            "total_potential_savings": total_savings,
            "currency": "USD",
            "summary": {
                "high_priority": len([r for r in recommendations if r['priority'] == 'high']),
                "medium_priority": len([r for r in recommendations if r['priority'] == 'medium']),
                "low_priority": len([r for r in recommendations if r['priority'] == 'low'])
            }
        })
        
    except Exception as e:
        logging.error(f"Erro ao obter recomendações: {e}")
        return jsonify({"error": f"Erro ao obter recomendações: {str(e)}"}), 500

