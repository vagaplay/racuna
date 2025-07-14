import React, { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell, BarChart, Bar } from 'recharts';
import './BudgetPageReal.css';

const BudgetPageAdvanced = () => {
  const [currentCosts, setCurrentCosts] = useState(null);
  const [forecast, setForecast] = useState(null);
  const [budgets, setBudgets] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [recommendations, setRecommendations] = useState(null);
  const [utilization, setUtilization] = useState(null);
  const [trends, setTrends] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('overview');

  const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000';

  useEffect(() => {
    loadAllData();
  }, []);

  const loadAllData = async () => {
    setLoading(true);
    try {
      await Promise.all([
        loadCurrentCosts(),
        loadForecast(),
        loadBudgets(),
        loadAlerts(),
        loadRecommendations(),
        loadUtilization(),
        loadTrends()
      ]);
    } catch (err) {
      setError('Erro ao carregar dados: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  const loadCurrentCosts = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/azure-budget/current-costs`, {
        credentials: 'include'
      });
      if (response.ok) {
        const data = await response.json();
        if (data.success) {
          setCurrentCosts(data.data);
        } else {
          console.error('Erro na API:', data.error);
        }
      } else if (response.status === 401) {
        setError('Usuário não autenticado. Faça login novamente.');
      }
    } catch (err) {
      console.error('Erro ao carregar custos atuais:', err);
    }
  };

  const loadForecast = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/azure-budget/forecast?days=30`, {
        credentials: 'include'
      });
      if (response.ok) {
        const data = await response.json();
        if (data.success) {
          setForecast(data.data);
        }
      } else if (response.status === 401) {
        setError('Usuário não autenticado. Faça login novamente.');
      }
    } catch (err) {
      console.error('Erro ao carregar previsão:', err);
    }
  };

  const loadBudgets = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/azure-budget/status`, {
        credentials: 'include'
      });
      if (response.ok) {
        const data = await response.json();
        if (data.success) {
          setBudgets([data.data]); // Status geral como um "orçamento"
        }
      } else if (response.status === 401) {
        setError('Usuário não autenticado. Faça login novamente.');
      }
    } catch (err) {
      console.error('Erro ao carregar orçamentos:', err);
    }
  };

  const loadAlerts = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/azure-budget/alerts`, {
        credentials: 'include'
      });
      if (response.ok) {
        const data = await response.json();
        setAlerts(data.alerts || []);
      }
    } catch (err) {
      console.error('Erro ao carregar alertas:', err);
    }
  };

  const loadRecommendations = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/azure-budget/recommendations`, {
        credentials: 'include'
      });
      if (response.ok) {
        const data = await response.json();
        setRecommendations(data);
      }
    } catch (err) {
      console.error('Erro ao carregar recomendações:', err);
    }
  };

  const loadUtilization = async () => {
    try {
      // Simular dados de utilização
      setUtilization({
        summary: {
          total_resources: 45,
          underutilized: 12,
          overutilized: 3,
          optimal: 30,
          utilization_score: 72
        },
        virtual_machines: [
          {
            name: "vm-web-01",
            cpu_avg: 15.5,
            memory_avg: 22.3,
            status: "underutilized",
            potential_savings: 45.20
          },
          {
            name: "vm-db-prod",
            cpu_avg: 85.2,
            memory_avg: 78.9,
            status: "optimal",
            potential_savings: 0
          }
        ]
      });
    } catch (err) {
      console.error('Erro ao carregar utilização:', err);
    }
  };

  const loadTrends = async () => {
    try {
      // Simular dados de tendência
      setTrends({
        monthly_costs: [
          { month: "Jan", cost: 1205.25 },
          { month: "Fev", cost: 1189.75 },
          { month: "Mar", cost: 1225.80 },
          { month: "Abr", cost: 1198.45 },
          { month: "Mai", cost: 1250.75 },
          { month: "Jun", cost: 1280.50 }
        ],
        trend_direction: "increasing",
        trend_percentage: 2.8
      });
    } catch (err) {
      console.error('Erro ao carregar tendências:', err);
    }
  };

  const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8'];

  if (loading) {
    return (
      <div className="budget-page">
        <div className="loading-container">
          <div className="loading-spinner"></div>
          <p>Carregando dados de orçamento...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="budget-page">
        <div className="error-container">
          <h3>❌ Erro</h3>
          <p>{error}</p>
          <button onClick={loadAllData} className="retry-button">
            🔄 Tentar Novamente
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="budget-page">
      <div className="budget-header">
        <h1>💰 Orçamento e Custos Azure</h1>
        <p>Análise avançada de custos, previsões e otimizações</p>
      </div>

      {/* Tabs de navegação */}
      <div className="budget-tabs">
        <button 
          className={`tab ${activeTab === 'overview' ? 'active' : ''}`}
          onClick={() => setActiveTab('overview')}
        >
          📊 Visão Geral
        </button>
        <button 
          className={`tab ${activeTab === 'forecast' ? 'active' : ''}`}
          onClick={() => setActiveTab('forecast')}
        >
          📈 Previsões
        </button>
        <button 
          className={`tab ${activeTab === 'optimization' ? 'active' : ''}`}
          onClick={() => setActiveTab('optimization')}
        >
          🎯 Otimização
        </button>
        <button 
          className={`tab ${activeTab === 'alerts' ? 'active' : ''}`}
          onClick={() => setActiveTab('alerts')}
        >
          🚨 Alertas
        </button>
      </div>

      {/* Conteúdo das tabs */}
      {activeTab === 'overview' && (
        <div className="tab-content">
          {/* Cards de resumo */}
          <div className="budget-summary">
            <div className="summary-card">
              <h3>💵 Custo Atual</h3>
              <div className="cost-value">
                ${currentCosts?.total_cost?.toFixed(2) || '0.00'}
              </div>
              <div className="cost-period">Este mês</div>
            </div>

            <div className="summary-card">
              <h3>📈 Previsão</h3>
              <div className="cost-value">
                ${forecast?.estimated_total?.toFixed(2) || '0.00'}
              </div>
              <div className="cost-period">Próximos 30 dias</div>
            </div>

            <div className="summary-card">
              <h3>💡 Economia Potencial</h3>
              <div className="cost-value savings">
                ${recommendations?.total_potential_savings?.toFixed(2) || '0.00'}
              </div>
              <div className="cost-period">Com otimizações</div>
            </div>

            <div className="summary-card">
              <h3>📊 Score de Utilização</h3>
              <div className="cost-value">
                {utilization?.summary?.utilization_score || 0}%
              </div>
              <div className="cost-period">Eficiência geral</div>
            </div>
          </div>

          {/* Gráficos */}
          <div className="charts-container">
            {/* Breakdown por serviço */}
            <div className="chart-card">
              <h3>📊 Custos por Serviço</h3>
              {currentCosts?.breakdown && (
                <ResponsiveContainer width="100%" height={300}>
                  <PieChart>
                    <Pie
                      data={currentCosts.breakdown}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      label={({name, percentage}) => `${name}: ${percentage}%`}
                      outerRadius={80}
                      fill="#8884d8"
                      dataKey="cost"
                    >
                      {currentCosts.breakdown.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip formatter={(value) => [`$${value}`, 'Custo']} />
                  </PieChart>
                </ResponsiveContainer>
              )}
            </div>

            {/* Tendência mensal */}
            <div className="chart-card">
              <h3>📈 Tendência de Custos</h3>
              {trends?.monthly_costs && (
                <ResponsiveContainer width="100%" height={300}>
                  <LineChart data={trends.monthly_costs}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="month" />
                    <YAxis />
                    <Tooltip formatter={(value) => [`$${value}`, 'Custo']} />
                    <Legend />
                    <Line 
                      type="monotone" 
                      dataKey="cost" 
                      stroke="#8884d8" 
                      strokeWidth={2}
                      name="Custo Mensal"
                    />
                  </LineChart>
                </ResponsiveContainer>
              )}
            </div>
          </div>

          {/* Lista de orçamentos */}
          <div className="budgets-list">
            <h3>📋 Orçamentos Ativos</h3>
            {budgets.length > 0 ? (
              <div className="budgets-grid">
                {budgets.map((budget) => (
                  <div key={budget.id} className="budget-card">
                    <h4>{budget.name}</h4>
                    <div className="budget-progress">
                      <div className="progress-bar">
                        <div 
                          className="progress-fill"
                          style={{ 
                            width: `${budget.percentage_used}%`,
                            backgroundColor: budget.percentage_used > 90 ? '#ff4444' : 
                                           budget.percentage_used > 80 ? '#ffaa00' : '#00aa44'
                          }}
                        ></div>
                      </div>
                      <div className="progress-text">
                        ${budget.current_spend} / ${budget.amount} ({budget.percentage_used.toFixed(1)}%)
                      </div>
                    </div>
                    <div className="budget-status">
                      Status: <span className={`status ${budget.status}`}>{budget.status}</span>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="no-budgets">
                <p>Nenhum orçamento configurado</p>
                <button className="create-budget-btn">
                  ➕ Criar Primeiro Orçamento
                </button>
              </div>
            )}
          </div>
        </div>
      )}

      {activeTab === 'forecast' && (
        <div className="tab-content">
          <div className="forecast-container">
            <h3>📈 Previsão de Custos - Próximos 30 dias</h3>
            
            {forecast && (
              <>
                <div className="forecast-summary">
                  <div className="forecast-card">
                    <h4>💰 Total Estimado</h4>
                    <div className="forecast-value">${forecast.estimated_total}</div>
                    <div className="forecast-confidence">
                      Confiança: {forecast.confidence_level}%
                    </div>
                  </div>
                  
                  <div className="forecast-card">
                    <h4>📊 Média Diária</h4>
                    <div className="forecast-value">${forecast.current_daily_average}</div>
                    <div className="forecast-trend">
                      Tendência: +{forecast.growth_rate_percentage}%
                    </div>
                  </div>
                </div>

                {forecast.weekly_forecast && (
                  <div className="chart-card">
                    <h4>📅 Previsão Semanal</h4>
                    <ResponsiveContainer width="100%" height={300}>
                      <BarChart data={forecast.weekly_forecast}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="week" />
                        <YAxis />
                        <Tooltip formatter={(value) => [`$${value}`, 'Custo Estimado']} />
                        <Bar dataKey="estimated_cost" fill="#8884d8" />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                )}

                <div className="forecast-factors">
                  <h4>🔍 Fatores Considerados</h4>
                  <ul>
                    {forecast.factors?.map((factor, index) => (
                      <li key={index}>{factor}</li>
                    ))}
                  </ul>
                </div>
              </>
            )}
          </div>
        </div>
      )}

      {activeTab === 'optimization' && (
        <div className="tab-content">
          <div className="optimization-container">
            <h3>🎯 Oportunidades de Otimização</h3>
            
            {recommendations && (
              <>
                <div className="optimization-summary">
                  <div className="optimization-card">
                    <h4>💰 Economia Total Potencial</h4>
                    <div className="savings-value">${recommendations.total_potential_savings}</div>
                    <div className="savings-period">Por mês</div>
                  </div>
                </div>

                <div className="recommendations-list">
                  {recommendations.categories?.map((category, index) => (
                    <div key={index} className="category-card">
                      <h4>{category.category}</h4>
                      <div className="category-savings">
                        Economia: ${category.potential_savings}
                      </div>
                      <div className="category-priority">
                        Prioridade: <span className={`priority ${category.priority}`}>
                          {category.priority}
                        </span>
                      </div>
                      
                      <div className="recommendations">
                        {category.recommendations?.map((rec, recIndex) => (
                          <div key={recIndex} className="recommendation-item">
                            <h5>{rec.title}</h5>
                            <p>{rec.description}</p>
                            <div className="rec-details">
                              <span className="rec-savings">💰 ${rec.savings}</span>
                              <span className="rec-resources">
                                📦 {rec.affected_resources} recursos
                              </span>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>

                {recommendations.quick_wins && (
                  <div className="quick-wins">
                    <h4>⚡ Ações Rápidas</h4>
                    <div className="quick-wins-list">
                      {recommendations.quick_wins.map((win, index) => (
                        <div key={index} className="quick-win-item">
                          <div className="win-action">{win.action || win}</div>
                          {win.savings && (
                            <div className="win-savings">${win.savings}/mês</div>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </>
            )}
          </div>
        </div>
      )}

      {activeTab === 'alerts' && (
        <div className="tab-content">
          <div className="alerts-container">
            <h3>🚨 Alertas de Orçamento</h3>
            
            {alerts.length > 0 ? (
              <div className="alerts-list">
                {alerts.map((alert) => (
                  <div key={alert.id} className={`alert-card ${alert.type}`}>
                    <div className="alert-header">
                      <h4>{alert.budget_name}</h4>
                      <span className={`alert-severity ${alert.severity}`}>
                        {alert.severity}
                      </span>
                    </div>
                    <div className="alert-message">{alert.message}</div>
                    <div className="alert-details">
                      <span>Limite: {alert.threshold}%</span>
                      <span>Atual: {alert.current_percentage}%</span>
                      <span>Data: {new Date(alert.created_at).toLocaleDateString()}</span>
                    </div>
                    {!alert.acknowledged && (
                      <button className="acknowledge-btn">
                        ✓ Reconhecer
                      </button>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <div className="no-alerts">
                <p>✅ Nenhum alerta ativo</p>
                <p>Todos os orçamentos estão dentro dos limites configurados.</p>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default BudgetPageAdvanced;

