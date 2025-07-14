import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar } from 'recharts';

const MonitoringPage = () => {
  const [metrics, setMetrics] = useState({
    resources: { total: 0, running: 0, stopped: 0 },
    costs: { today: 0, month: 0, trend: [] },
    alerts: [],
    activities: []
  });
  const [loading, setLoading] = useState(false);
  const [timeRange, setTimeRange] = useState('24h');
  const [hasCredentials, setHasCredentials] = useState(false);
  const [checkingCredentials, setCheckingCredentials] = useState(true);
  
  const navigate = useNavigate();
  const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5001';

  const checkCredentialsStatus = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/azure/credentials-status`, {
        credentials: 'include'
      });
      
      if (response.ok) {
        const data = await response.json();
        setHasCredentials(data.configured);
      }
    } catch (error) {
      console.error('Erro ao verificar credenciais:', error);
      setHasCredentials(false);
    } finally {
      setCheckingCredentials(false);
    }
  };

  const loadMetrics = async () => {
    if (!hasCredentials) return;
    
    setLoading(true);
    try {
      const response = await fetch(`${API_BASE_URL}/api/monitoring/metrics?range=${timeRange}`, {
        credentials: 'include'
      });
      if (response.ok) {
        const data = await response.json();
        setMetrics(data);
      }
    } catch (error) {
      console.error('Erro ao carregar métricas:', error);
    }
    setLoading(false);
  };

  const acknowledgeAlert = async (alertId) => {
    try {
      await fetch(`${API_BASE_URL}/api/monitoring/alerts/${alertId}/acknowledge`, {
        method: 'POST',
        credentials: 'include'
      });
      await loadMetrics();
    } catch (error) {
      console.error('Erro ao reconhecer alerta:', error);
    }
  };

  useEffect(() => {
    checkCredentialsStatus();
  }, []);

  useEffect(() => {
    if (hasCredentials) {
      loadMetrics();
      const interval = setInterval(loadMetrics, 30000); // Atualizar a cada 30 segundos
      return () => clearInterval(interval);
    }
  }, [timeRange, hasCredentials]);

  const getAlertIcon = (severity) => {
    switch (severity) {
      case 'critical': return '🚨';
      case 'warning': return '⚠️';
      case 'info': return 'ℹ️';
      default: return '📢';
    }
  };

  const getAlertColor = (severity) => {
    switch (severity) {
      case 'critical': return 'bg-red-100 border-red-300 text-red-800';
      case 'warning': return 'bg-yellow-100 border-yellow-300 text-yellow-800';
      case 'info': return 'bg-blue-100 border-blue-300 text-blue-800';
      default: return 'bg-gray-100 border-gray-300 text-gray-800';
    }
  };

  return (
    <div className="p-6">
      {checkingCredentials ? (
        <div className="flex items-center justify-center min-h-[400px]">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
            <p className="text-gray-600">Verificando credenciais...</p>
          </div>
        </div>
      ) : !hasCredentials ? (
        <div className="flex items-center justify-center min-h-[400px]">
          <div className="text-center max-w-md">
            <div className="text-6xl mb-4">⚙️</div>
            <h2 className="text-2xl font-bold text-gray-800 mb-4">Credenciais Azure Não Configuradas</h2>
            <p className="text-gray-600 mb-6">
              Para visualizar os dados de monitoramento do Azure, você precisa configurar suas credenciais primeiro.
            </p>
            <button
              onClick={() => navigate('/azure-config')}
              className="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 transition-colors"
            >
              Configurar Credenciais Azure
            </button>
          </div>
        </div>
      ) : (
        <>
          <div className="flex justify-between items-center mb-6">
            <h1 className="text-3xl font-bold">📊 Monitoramento e Alertas</h1>
            <div className="flex gap-2">
              <select
                value={timeRange}
                onChange={(e) => setTimeRange(e.target.value)}
                className="border rounded-lg px-3 py-2"
              >
                <option value="1h">Última Hora</option>
                <option value="24h">Últimas 24h</option>
                <option value="7d">Últimos 7 dias</option>
                <option value="30d">Últimos 30 dias</option>
              </select>
              <button
                onClick={loadMetrics}
                disabled={loading}
                className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50"
              >
                {loading ? '🔄' : '🔄'} Atualizar
              </button>
            </div>
      </div>

      {/* Cards de Métricas Principais */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-6">
        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Total de Recursos</p>
              <p className="text-3xl font-bold">{metrics.resources.total}</p>
            </div>
            <div className="text-4xl">🏗️</div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Recursos Ativos</p>
              <p className="text-3xl font-bold text-green-600">{metrics.resources.running}</p>
            </div>
            <div className="text-4xl">✅</div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Recursos Parados</p>
              <p className="text-3xl font-bold text-gray-600">{metrics.resources.stopped}</p>
            </div>
            <div className="text-4xl">⏸️</div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Custo do Mês</p>
              <p className="text-3xl font-bold text-blue-600">R$ {metrics.costs.month.toFixed(2)}</p>
            </div>
            <div className="text-4xl">💰</div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        {/* Gráfico de Custos */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold mb-4">📈 Tendência de Custos</h2>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={metrics.costs.trend}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis />
              <Tooltip formatter={(value) => [`R$ ${value.toFixed(2)}`, 'Custo']} />
              <Line type="monotone" dataKey="cost" stroke="#3B82F6" strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Gráfico de Recursos por Tipo */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold mb-4">🏗️ Recursos por Tipo</h2>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={metrics.resourcesByType || []}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="type" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="count" fill="#10B981" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Alertas Ativos */}
      <div className="bg-white rounded-lg shadow-md p-6 mb-6">
        <h2 className="text-xl font-semibold mb-4">🚨 Alertas Ativos</h2>
        
        {metrics.alerts.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            <p className="text-xl mb-2">✅ Nenhum alerta ativo</p>
            <p>Todos os sistemas estão funcionando normalmente</p>
          </div>
        ) : (
          <div className="space-y-3">
            {metrics.alerts.map(alert => (
              <div key={alert.id} className={`border rounded-lg p-4 ${getAlertColor(alert.severity)}`}>
                <div className="flex justify-between items-start">
                  <div className="flex items-start gap-3">
                    <span className="text-2xl">{getAlertIcon(alert.severity)}</span>
                    <div>
                      <h3 className="font-semibold">{alert.title}</h3>
                      <p className="text-sm mt-1">{alert.message}</p>
                      <p className="text-xs mt-2 opacity-75">
                        {new Date(alert.created_at).toLocaleString()}
                      </p>
                    </div>
                  </div>
                  <button
                    onClick={() => acknowledgeAlert(alert.id)}
                    className="px-3 py-1 bg-white bg-opacity-50 rounded text-sm hover:bg-opacity-75"
                  >
                    ✓ Reconhecer
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Atividades Recentes */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <h2 className="text-xl font-semibold mb-4">📋 Atividades Recentes</h2>
        
        {metrics.activities.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            <p>Nenhuma atividade recente</p>
          </div>
        ) : (
          <div className="space-y-3">
            {metrics.activities.map((activity, index) => (
              <div key={index} className="flex items-center gap-3 p-3 border rounded-lg">
                <span className="text-2xl">{activity.icon}</span>
                <div className="flex-1">
                  <p className="font-medium">{activity.title}</p>
                  <p className="text-sm text-gray-600">{activity.description}</p>
                </div>
                <span className="text-sm text-gray-500">
                  {new Date(activity.timestamp).toLocaleString()}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Status de Saúde dos Serviços */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-6">
        <div className="bg-white rounded-lg shadow-md p-6">
          <h3 className="text-lg font-semibold mb-3">🔄 Azure Functions</h3>
          <div className="flex items-center gap-2">
            <span className="w-3 h-3 bg-green-500 rounded-full"></span>
            <span className="text-sm">Operacional</span>
          </div>
          <p className="text-xs text-gray-600 mt-2">Última execução: há 5 minutos</p>
        </div>

        <div className="bg-white rounded-lg shadow-md p-6">
          <h3 className="text-lg font-semibold mb-3">💰 Cost Management</h3>
          <div className="flex items-center gap-2">
            <span className="w-3 h-3 bg-green-500 rounded-full"></span>
            <span className="text-sm">Operacional</span>
          </div>
          <p className="text-xs text-gray-600 mt-2">Última sincronização: há 2 horas</p>
        </div>

        <div className="bg-white rounded-lg shadow-md p-6">
          <h3 className="text-lg font-semibold mb-3">🔐 Resource Management</h3>
          <div className="flex items-center gap-2">
            <span className="w-3 h-3 bg-green-500 rounded-full"></span>
            <span className="text-sm">Operacional</span>
          </div>
          <p className="text-xs text-gray-600 mt-2">Última verificação: há 1 minuto</p>
        </div>
      </div>
        </>
      )}
    </div>
  );
};

export default MonitoringPage;

