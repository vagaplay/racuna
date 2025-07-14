import React, { useState, useEffect } from 'react';
import './AzureFunctionsConfigPage.css';

const AzureFunctionsConfigPage = () => {
  const [config, setConfig] = useState({
    lockCheckDay: 2,
    shutdownHour: 19,
    tagCheckHour: 19,
    budgetAmount: 200.0,
    budgetCurrency: 'USD',
    budgetStartDate: new Date().toISOString().split('T')[0],
    budgetEndDate: new Date(new Date().getFullYear(), 11, 31).toISOString().split('T')[0],
    timezone: 'America/Sao_Paulo',
    requiredTags: 'Environment,Owner,Project'
  });

  const [status, setStatus] = useState({
    loading: false,
    message: '',
    type: '' // 'success' or 'error'
  });

  const [currentConfig, setCurrentConfig] = useState(null);
  useEffect(() => {
    checkAuthAndLoadConfigurations();
  }, []);

  const checkAuthAndLoadConfigurations = async () => {
    try {
      setLoading(true);
      setError('');

      // Verificar autenticação primeiro
      const authResponse = await fetch(`${API_BASE_URL}/api/auth/status`, {
        method: 'GET',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
        }
      });

      if (!authResponse.ok) {
        setError('Usuário não autenticado. Faça login novamente.');
        setLoading(false);
        return;
      }

      const authData = await authResponse.json();
      if (!authData.authenticated) {
        setError('Usuário não autenticado. Faça login novamente.');
        setLoading(false);
        return;
      }

      // Verificar se credenciais Azure estão configuradas
      const credentialsResponse = await fetch(`${API_BASE_URL}/api/azure/credentials-status`, {
        credentials: 'include'
      });
      
      if (!credentialsResponse.ok) {
        setError('Erro ao verificar credenciais Azure');
        setLoading(false);
        return;
      }
      
      const credentialsData = await credentialsResponse.json();

      if (!credentialsData.configured) {
        setError('Credenciais Azure não configuradas. Configure primeiro na página de Config. Azure.');
        setLoading(false);
        return;
      }

      // Carregar configurações das Azure Functions
      await loadConfigurations();

    } catch (error) {
      console.error('Erro ao carregar configurações:', error);
      setError('Erro ao carregar configurações: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  const loadCurrentConfig = async () => {
    try {
      setStatus({ loading: true, message: 'Carregando configurações...', type: '' });
      
      const response = await fetch('/api/azure-functions/config', {
        credentials: 'include'
      });

      if (response.ok) {
        const data = await response.json();
        setCurrentConfig(data);
        
        // Atualizar formulário com configurações atuais
        if (data.config) {
          setConfig(prev => ({
            ...prev,
            ...data.config
          }));
        }
        
        setStatus({ loading: false, message: 'Configurações carregadas com sucesso', type: 'success' });
      } else {
        setStatus({ loading: false, message: 'Erro ao carregar configurações', type: 'error' });
      }
    } catch (error) {
      setStatus({ loading: false, message: 'Erro de conexão ao carregar configurações', type: 'error' });
    }
  };

  const handleInputChange = (e) => {
    const { name, value, type } = e.target;
    setConfig(prev => ({
      ...prev,
      [name]: type === 'number' ? parseFloat(value) || 0 : value
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    try {
      setStatus({ loading: true, message: 'Salvando configurações...', type: '' });
      
      const response = await fetch('/api/azure-functions/config', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        credentials: 'include',
        body: JSON.stringify(config)
      });

      if (response.ok) {
        const data = await response.json();
        setCurrentConfig(data);
        setStatus({ loading: false, message: 'Configurações salvas com sucesso!', type: 'success' });
      } else {
        const errorData = await response.json();
        setStatus({ loading: false, message: errorData.error || 'Erro ao salvar configurações', type: 'error' });
      }
    } catch (error) {
      setStatus({ loading: false, message: 'Erro de conexão ao salvar configurações', type: 'error' });
    }
  };

  const testFunction = async (functionName) => {
    try {
      setStatus({ loading: true, message: `Testando ${functionName}...`, type: '' });
      
      const response = await fetch(`/api/azure-functions/test/${functionName}`, {
        method: 'POST',
        credentials: 'include'
      });

      if (response.ok) {
        const data = await response.json();
        setStatus({ loading: false, message: `Teste de ${functionName} executado com sucesso!`, type: 'success' });
      } else {
        const errorData = await response.json();
        setStatus({ loading: false, message: errorData.error || `Erro no teste de ${functionName}`, type: 'error' });
      }
    } catch (error) {
      setStatus({ loading: false, message: `Erro de conexão no teste de ${functionName}`, type: 'error' });
    }
  };

  const generateCronExpression = (day, hour) => {
    return `0 0 ${hour} ${day} * *`;
  };

  return (
    <div className="azure-functions-config-page">
      <div className="page-header">
        <h1>⚙️ Configuração das Azure Functions</h1>
        <p>Configure os parâmetros de execução das funções de automação Azure</p>
      </div>

      {status.message && (
        <div className={`status-message ${status.type}`}>
          {status.loading && <div className="spinner"></div>}
          {status.message}
        </div>
      )}

      <div className="config-container">
        <div className="config-section">
          <h2>📅 Configurações de Agendamento</h2>
          
          <form onSubmit={handleSubmit} className="config-form">
            <div className="form-group">
              <label htmlFor="lockCheckDay">
                🔒 Dia de Verificação de Lock (1-31)
                <span className="help-text">Dia do mês para verificar e remover lock da subscription</span>
              </label>
              <input
                type="number"
                id="lockCheckDay"
                name="lockCheckDay"
                min="1"
                max="31"
                value={config.lockCheckDay}
                onChange={handleInputChange}
                required
              />
              <small>Expressão cron: {generateCronExpression(config.lockCheckDay, 8)}</small>
            </div>

            <div className="form-group">
              <label htmlFor="shutdownHour">
                🌙 Horário de Shutdown (0-23)
                <span className="help-text">Hora para desligar recursos automaticamente (seg-sex)</span>
              </label>
              <input
                type="number"
                id="shutdownHour"
                name="shutdownHour"
                min="0"
                max="23"
                value={config.shutdownHour}
                onChange={handleInputChange}
                required
              />
              <small>Expressão cron: 0 0 {config.shutdownHour} * * 1-5</small>
            </div>

            <div className="form-group">
              <label htmlFor="tagCheckHour">
                🏷️ Horário de Verificação de Tags (0-23)
                <span className="help-text">Hora para verificar recursos sem tags (seg-sex)</span>
              </label>
              <input
                type="number"
                id="tagCheckHour"
                name="tagCheckHour"
                min="0"
                max="23"
                value={config.tagCheckHour}
                onChange={handleInputChange}
                required
              />
              <small>Expressão cron: 0 0 {config.tagCheckHour} * * 1-5</small>
            </div>

            <div className="form-group">
              <label htmlFor="requiredTags">
                🏷️ Tags Obrigatórias
                <span className="help-text">Tags separadas por vírgula (ex: Environment,Owner,Project)</span>
              </label>
              <input
                type="text"
                id="requiredTags"
                name="requiredTags"
                value={config.requiredTags}
                onChange={handleInputChange}
                placeholder="Environment,Owner,Project"
                required
              />
            </div>
          </form>
        </div>

        <div className="config-section">
          <h2>💰 Configurações de Budget</h2>
          
          <div className="form-group">
            <label htmlFor="budgetAmount">
              💵 Valor do Budget
              <span className="help-text">Limite de gastos mensais</span>
            </label>
            <input
              type="number"
              id="budgetAmount"
              name="budgetAmount"
              min="0"
              step="0.01"
              value={config.budgetAmount}
              onChange={handleInputChange}
              required
            />
          </div>

          <div className="form-group">
            <label htmlFor="budgetCurrency">
              💱 Moeda
            </label>
            <select
              id="budgetCurrency"
              name="budgetCurrency"
              value={config.budgetCurrency}
              onChange={handleInputChange}
              required
            >
              <option value="USD">USD - Dólar Americano</option>
              <option value="BRL">BRL - Real Brasileiro</option>
              <option value="EUR">EUR - Euro</option>
            </select>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label htmlFor="budgetStartDate">
                📅 Data Início
              </label>
              <input
                type="date"
                id="budgetStartDate"
                name="budgetStartDate"
                value={config.budgetStartDate}
                onChange={handleInputChange}
                required
              />
            </div>

            <div className="form-group">
              <label htmlFor="budgetEndDate">
                📅 Data Fim
              </label>
              <input
                type="date"
                id="budgetEndDate"
                name="budgetEndDate"
                value={config.budgetEndDate}
                onChange={handleInputChange}
                required
              />
            </div>
          </div>
        </div>

        <div className="config-section">
          <h2>🌍 Configurações Gerais</h2>
          
          <div className="form-group">
            <label htmlFor="timezone">
              🕐 Timezone
            </label>
            <select
              id="timezone"
              name="timezone"
              value={config.timezone}
              onChange={handleInputChange}
              required
            >
              <option value="America/Sao_Paulo">America/Sao_Paulo (UTC-3)</option>
              <option value="UTC">UTC (UTC+0)</option>
              <option value="America/New_York">America/New_York (UTC-5)</option>
              <option value="Europe/London">Europe/London (UTC+0)</option>
            </select>
          </div>
        </div>

        <div className="form-actions">
          <button 
            type="submit" 
            onClick={handleSubmit}
            className="btn-primary"
            disabled={status.loading}
          >
            {status.loading ? 'Salvando...' : '💾 Salvar Configurações'}
          </button>
          
          <button 
            type="button" 
            onClick={loadCurrentConfig}
            className="btn-secondary"
            disabled={status.loading}
          >
            🔄 Recarregar
          </button>
        </div>
      </div>

      {currentConfig && (
        <div className="current-config">
          <h2>📊 Configuração Atual</h2>
          <div className="config-summary">
            <div className="summary-item">
              <strong>🔒 Verificação de Lock:</strong> Dia {currentConfig.lock_check_day} às 8h
            </div>
            <div className="summary-item">
              <strong>🌙 Shutdown:</strong> {currentConfig.shutdown_hour}h (seg-sex)
            </div>
            <div className="summary-item">
              <strong>🏷️ Verificação de Tags:</strong> {currentConfig.tag_check_hour}h (seg-sex)
            </div>
            <div className="summary-item">
              <strong>💰 Budget:</strong> {currentConfig.budget_currency} {currentConfig.budget_amount}
            </div>
          </div>
        </div>
      )}

      <div className="test-functions">
        <h2>🧪 Testar Functions</h2>
        <div className="test-buttons">
          <button 
            onClick={() => testFunction('lock-check')}
            className="btn-test"
            disabled={status.loading}
          >
            🔒 Testar Verificação de Lock
          </button>
          
          <button 
            onClick={() => testFunction('cleanup-resources')}
            className="btn-test"
            disabled={status.loading}
          >
            🧹 Testar Limpeza de Recursos
          </button>
          
          <button 
            onClick={() => testFunction('budget-exceeded')}
            className="btn-test"
            disabled={status.loading}
          >
            💰 Testar Budget Excedido
          </button>
        </div>
      </div>
    </div>
  );
};

export default AzureFunctionsConfigPage;

