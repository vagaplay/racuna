"""
Azure Cost Management - Integração Real
Conecta com APIs reais do Azure para dados de custos
"""

from azure.mgmt.consumption import ConsumptionManagementClient
from azure.mgmt.costmanagement import CostManagementClient
from azure.identity import DefaultAzureCredential, ClientSecretCredential
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class AzureCostRealService:
    def __init__(self, tenant_id, client_id, client_secret, subscription_id):
        """Inicializar serviço com credenciais reais"""
        self.tenant_id = tenant_id
        self.client_id = client_id
        self.client_secret = client_secret
        self.subscription_id = subscription_id
        
        # Criar credencial
        self.credential = ClientSecretCredential(
            tenant_id=tenant_id,
            client_id=client_id,
            client_secret=client_secret
        )
        
        # Inicializar clientes
        try:
            self.consumption_client = ConsumptionManagementClient(
                credential=self.credential,
                subscription_id=subscription_id
            )
            self.cost_client = CostManagementClient(
                credential=self.credential
            )
        except Exception as e:
            logger.error(f"Erro ao inicializar clientes Azure: {e}")
            self.consumption_client = None
            self.cost_client = None

    def get_current_costs(self):
        """Obter custos atuais reais do Azure"""
        try:
            if not self.consumption_client:
                return self._get_empty_costs()
            
            # Definir período (último mês)
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30)
            
            # Buscar dados de uso
            usage_details = self.consumption_client.usage_details.list(
                scope=f"/subscriptions/{self.subscription_id}",
                filter=f"properties/usageStart ge '{start_date.strftime('%Y-%m-%d')}' and properties/usageEnd le '{end_date.strftime('%Y-%m-%d')}'"
            )
            
            total_cost = 0
            daily_costs = {}
            service_costs = {}
            
            for usage in usage_details:
                if hasattr(usage, 'cost') and usage.cost:
                    total_cost += float(usage.cost)
                    
                    # Agrupar por dia
                    usage_date = usage.date.strftime('%Y-%m-%d') if hasattr(usage, 'date') else 'unknown'
                    if usage_date not in daily_costs:
                        daily_costs[usage_date] = 0
                    daily_costs[usage_date] += float(usage.cost)
                    
                    # Agrupar por serviço
                    service_name = getattr(usage, 'meter_category', 'Unknown')
                    if service_name not in service_costs:
                        service_costs[service_name] = 0
                    service_costs[service_name] += float(usage.cost)
            
            return {
                'success': True,
                'data': {
                    'total_cost': total_cost,
                    'currency': 'USD',
                    'period': {
                        'start': start_date.isoformat(),
                        'end': end_date.isoformat()
                    },
                    'daily_costs': [
                        {'date': date, 'cost': cost}
                        for date, cost in sorted(daily_costs.items())
                    ],
                    'service_breakdown': [
                        {'service': service, 'cost': cost}
                        for service, cost in sorted(service_costs.items(), key=lambda x: x[1], reverse=True)
                    ]
                }
            }
            
        except Exception as e:
            logger.error(f"Erro ao obter custos reais: {e}")
            return self._get_empty_costs()
    
    def get_budget_status(self):
        """Obter status de orçamentos reais"""
        try:
            if not self.cost_client:
                return self._get_empty_budgets()
            
            # Buscar orçamentos
            budgets = self.cost_client.budgets.list(
                scope=f"/subscriptions/{self.subscription_id}"
            )
            
            budget_list = []
            for budget in budgets:
                budget_info = {
                    'name': budget.name,
                    'amount': float(budget.amount) if hasattr(budget, 'amount') else 0,
                    'current_spend': 0,  # Seria calculado com base nos custos atuais
                    'percentage_used': 0,
                    'status': 'active' if hasattr(budget, 'status') and budget.status == 'Enabled' else 'inactive',
                    'time_period': {
                        'start': budget.time_period.start_date.isoformat() if hasattr(budget, 'time_period') else None,
                        'end': budget.time_period.end_date.isoformat() if hasattr(budget, 'time_period') else None
                    }
                }
                budget_list.append(budget_info)
            
            return {
                'success': True,
                'data': {
                    'budgets': budget_list,
                    'total_budgets': len(budget_list)
                }
            }
            
        except Exception as e:
            logger.error(f"Erro ao obter orçamentos: {e}")
            return self._get_empty_budgets()
    
    def get_cost_forecast(self, days=30):
        """Obter previsão de custos"""
        try:
            # Para conta nova/vazia, previsão será baseada em dados históricos
            current_costs = self.get_current_costs()
            
            if not current_costs['success'] or current_costs['data']['total_cost'] == 0:
                # Conta vazia - previsão zero
                forecast_data = []
                for i in range(days):
                    future_date = datetime.now() + timedelta(days=i+1)
                    forecast_data.append({
                        'date': future_date.strftime('%Y-%m-%d'),
                        'estimated_cost': 0.0,
                        'confidence': 100  # 100% de confiança para zero
                    })
                
                return {
                    'success': True,
                    'data': {
                        'daily_forecast': forecast_data,
                        'total_forecast': 0.0,
                        'confidence_level': 100
                    }
                }
            
            # Se houver dados históricos, calcular previsão baseada na média
            daily_costs = current_costs['data']['daily_costs']
            if daily_costs:
                avg_daily_cost = sum(day['cost'] for day in daily_costs) / len(daily_costs)
                
                forecast_data = []
                for i in range(days):
                    future_date = datetime.now() + timedelta(days=i+1)
                    forecast_data.append({
                        'date': future_date.strftime('%Y-%m-%d'),
                        'estimated_cost': avg_daily_cost,
                        'confidence': max(50, 100 - (i * 2))  # Confiança diminui com o tempo
                    })
                
                return {
                    'success': True,
                    'data': {
                        'daily_forecast': forecast_data,
                        'total_forecast': avg_daily_cost * days,
                        'confidence_level': 75
                    }
                }
            
        except Exception as e:
            logger.error(f"Erro ao calcular previsão: {e}")
        
        # Fallback para previsão zero
        return {
            'success': True,
            'data': {
                'daily_forecast': [],
                'total_forecast': 0.0,
                'confidence_level': 100
            }
        }
    
    def _get_empty_costs(self):
        """Retornar estrutura vazia para conta sem custos"""
        return {
            'success': True,
            'data': {
                'total_cost': 0.0,
                'currency': 'USD',
                'period': {
                    'start': (datetime.now() - timedelta(days=30)).isoformat(),
                    'end': datetime.now().isoformat()
                },
                'daily_costs': [],
                'service_breakdown': []
            }
        }
    
    def _get_empty_budgets(self):
        """Retornar estrutura vazia para orçamentos"""
        return {
            'success': True,
            'data': {
                'budgets': [],
                'total_budgets': 0
            }
        }

