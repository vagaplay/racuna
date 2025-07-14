import React, { useState, useEffect } from 'react';
import './BudgetPageReal.css';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

const BudgetPageReal = () => {
  const [budgetData, setBudgetData] = useState(null);
  const [costData, setCostData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [newBudget, setNewBudget] = useState({
    name: '',
    amount: '',
    timeGrain: 'Monthly',
    startDate: '',
    endDate: ''
  });

  useEffect(() => {
    loadBudgetData();
    loadCostData();
  }, []);

  const loadBudgetData = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/azure-budget/list-budgets`, {
        credentials: 'include'
      });
      
      if (response.ok) {
        const data = await response.json();
        setBudgetData(data);
      } else {
        setError('Erro ao carregar dados de orçamento');
      }
    } catch (err) {
      setError('Erro de conexão ao carregar orçamentos');
    }
  };

  const loadCostData = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/azure-budget/current-costs`, {
        credentials: 'include'
      });
      
      if (response.ok) {
        const data = await response.json();
        setCostData(data);
      }
    } catch (err) {
      console.error('Erro ao carregar custos:', err);
    } finally {
      setLoading(false);
    }
  };

  const createBudget = async () => {
    if (!newBudget.name || !newBudget.amount) {
      alert('Nome e valor do orçamento são obrigatórios');
      return;
    }

    setLoading(true);
    try {
      const response = await fetch(`${API_BASE_URL}/api/azure-budget/create-budget`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        credentials: 'include',
        body: JSON.stringify(newBudget)
      });

      if (response.ok) {
        const result = await response.json();
        alert(`Orçamento "${newBudget.name}" criado com sucesso!`);
        setNewBudget({ name: '', amount: '', timeGrain: 'Monthly', startDate: '', endDate: '' });
        loadBudgetData();
      } else {
        const error = await response.json();
        alert(`Erro ao criar orçamento: ${error.error}`);
      }
    } catch (err) {
      alert('Erro de conexão ao criar orçamento');
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('pt-BR', {
      style: 'currency',
      currency: 'USD'
    }).format(value || 0);
  };

  const getUsagePercentage = (current, limit) => {
    return limit > 0 ? Math.min((current / limit) * 100, 100) : 0;
  };

  const getUsageColor = (percentage) => {
    if (percentage >= 90) return '#e74c3c';
    if (percentage >= 75) return '#f39c12';
    if (percentage >= 50) return '#f1c40f';
    return '#27ae60';
  };

  if (loading) {
    return (
      <div className="budget-page">
        <div className="loading">
          <h2>⏳ Carregando dados de orçamento...</h2>
          <p>Conectando com Azure Cost Management...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="budget-page">
      <div className="page-header">
        <h1>💰 Gerenciamento de Orçamento Azure</h1>
        <p>Monitore e controle seus gastos em tempo real</p>
      </div>

      {error && (
        <div className="error-banner">
          <h3>⚠️ {error}</h3>
          <p>Verifique suas credenciais Azure e permissões de Cost Management</p>
        </div>
      )}

      {/* Resumo de Custos Atuais */}
      {costData && (
        <div className="cost-summary">
          <h2>📊 Custos Atuais</h2>
          <div className="cost-cards">
            <div className="cost-card">
              <h3>💸 Gasto do Mês</h3>
              <div className="cost-value">{formatCurrency(costData.currentMonth)}</div>
              <p className="cost-period">Período atual</p>
            </div>
            <div className="cost-card">
              <h3>📈 Previsão</h3>
              <div className="cost-value">{formatCurrency(costData.forecast)}</div>
              <p className="cost-period">Fim do mês</p>
            </div>
            <div className="cost-card">
              <h3>📅 Mês Anterior</h3>
              <div className="cost-value">{formatCurrency(costData.lastMonth)}</div>
              <p className="cost-period">Comparação</p>
            </div>
          </div>
        </div>
      )}

      {/* Orçamentos Ativos */}
      {budgetData && budgetData.budgets && budgetData.budgets.length > 0 && (
        <div className="budgets-section">
          <h2>🎯 Orçamentos Ativos</h2>
          <div className="budgets-grid">
            {budgetData.budgets.map((budget, index) => {
              const percentage = getUsagePercentage(budget.currentSpend, budget.amount);
              const color = getUsageColor(percentage);
              
              return (
                <div key={index} className="budget-card">
                  <div className="budget-header">
                    <h3>{budget.name}</h3>
                    <span className="budget-period">{budget.timeGrain}</span>
                  </div>
                  
                  <div className="budget-progress">
                    <div className="progress-bar">
                      <div 
                        className="progress-fill" 
                        style={{ 
                          width: `${percentage}%`,
                          backgroundColor: color
                        }}
                      ></div>
                    </div>
                    <div className="progress-text">
                      {formatCurrency(budget.currentSpend)} / {formatCurrency(budget.amount)}
                      <span className="percentage">({percentage.toFixed(1)}%)</span>
                    </div>
                  </div>

                  <div className="budget-details">
                    <p><strong>Período:</strong> {budget.startDate} - {budget.endDate}</p>
                    {budget.alerts && budget.alerts.length > 0 && (
                      <div className="budget-alerts">
                        <h4>🚨 Alertas Configurados:</h4>
                        {budget.alerts.map((alert, i) => (
                          <p key={i}>• {alert.threshold}% - {alert.contactEmails.join(', ')}</p>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Criar Novo Orçamento */}
      <div className="create-budget-section">
        <h2>➕ Criar Novo Orçamento</h2>
        <div className="budget-form">
          <div className="form-row">
            <div className="form-group">
              <label>Nome do Orçamento:</label>
              <input
                type="text"
                value={newBudget.name}
                onChange={(e) => setNewBudget({...newBudget, name: e.target.value})}
                placeholder="Ex: Orçamento Desenvolvimento"
              />
            </div>
            <div className="form-group">
              <label>Valor Limite (USD):</label>
              <input
                type="number"
                value={newBudget.amount}
                onChange={(e) => setNewBudget({...newBudget, amount: e.target.value})}
                placeholder="Ex: 1000"
              />
            </div>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label>Período:</label>
              <select
                value={newBudget.timeGrain}
                onChange={(e) => setNewBudget({...newBudget, timeGrain: e.target.value})}
              >
                <option value="Monthly">Mensal</option>
                <option value="Quarterly">Trimestral</option>
                <option value="Annually">Anual</option>
              </select>
            </div>
            <div className="form-group">
              <label>Data Início:</label>
              <input
                type="date"
                value={newBudget.startDate}
                onChange={(e) => setNewBudget({...newBudget, startDate: e.target.value})}
              />
            </div>
            <div className="form-group">
              <label>Data Fim:</label>
              <input
                type="date"
                value={newBudget.endDate}
                onChange={(e) => setNewBudget({...newBudget, endDate: e.target.value})}
              />
            </div>
          </div>

          <button 
            onClick={createBudget}
            disabled={loading}
            className="create-budget-btn"
          >
            {loading ? '⏳ Criando...' : '💰 Criar Orçamento'}
          </button>
        </div>
      </div>

      {/* Dicas de Economia */}
      <div className="savings-tips">
        <h2>💡 Dicas de Economia</h2>
        <div className="tips-grid">
          <div className="tip-card">
            <h3>🔒 Use Locks</h3>
            <p>Proteja recursos críticos contra deleção acidental</p>
          </div>
          <div className="tip-card">
            <h3>⏰ Agendamentos</h3>
            <p>Configure shutdown automático fora do horário de trabalho</p>
          </div>
          <div className="tip-card">
            <h3>🏷️ Tags</h3>
            <p>Organize recursos por projeto para melhor controle</p>
          </div>
          <div className="tip-card">
            <h3>📊 Monitore</h3>
            <p>Revise custos semanalmente e ajuste conforme necessário</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default BudgetPageReal;

