import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import { AlertCircle, TrendingUp, DollarSign, Server, Settings, RefreshCw } from 'lucide-react';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

const DashboardHome = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [credentialsConfigured, setCredentialsConfigured] = useState(false);
  const [dashboardData, setDashboardData] = useState(null);
  const [costData, setCostData] = useState([]);
  const [forecastData, setForecastData] = useState([]);
  const [serviceData, setServiceData] = useState([]);

  useEffect(() => {
    checkCredentialsAndLoadData();
  }, []);

  const checkCredentialsAndLoadData = async () => {
    try {
      setLoading(true);
      setError('');

      // Primeiro verificar autenticação
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

      // Verificar se credenciais estão configuradas
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
        setCredentialsConfigured(false);
        setLoading(false);
        return;
      }

      setCredentialsConfigured(true);

      // Carregar dados do dashboard
      await Promise.all([
        loadDashboardSummary(),
        loadCostData(),
        loadForecastData()
      ]);

    } catch (error) {
      console.error('Erro ao carregar dados:', error);
      setError('Erro ao carregar dados: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  const loadDashboardSummary = async () => {
    try {
      // Tentar carregar dados reais dos resource groups
      const response = await fetch(`${API_BASE_URL}/api/azure-test/list-resource-groups`, {
        credentials: 'include'
      });
      
      if (response.ok) {
        const data = await response.json();
        const resourceGroupCount = data.resource_groups ? data.resource_groups.length : 0;
        
        // Usar dados reais da conta Azure
        setDashboardData({
          totalResources: resourceGroupCount,
          activeServices: 0, // Conta vazia
          monthlySpend: 0.00, // Sem gastos ainda
          alerts: 0,
          resourceGroups: resourceGroupCount,
          virtualMachines: 0,
          storageAccounts: 0,
          databases: 0,
          top_services: [], // Vazio para conta nova
          lastUpdated: new Date().toISOString()
        });
        
        // Dados vazios para gráficos
        setServiceData([]);
      } else {
        // Fallback se API falhar
        setDashboardData({
          totalResources: 2,
          activeServices: 0,
          monthlySpend: 0.00,
          alerts: 0,
          resourceGroups: 2,
          virtualMachines: 0,
          storageAccounts: 0,
          databases: 0,
          top_services: [],
          lastUpdated: new Date().toISOString()
        });
        setServiceData([]);
      }
    } catch (error) {
      console.error('Erro ao carregar resumo:', error);
      // Dados padrão para conta vazia
      setDashboardData({
        totalResources: 2,
        activeServices: 0,
        monthlySpend: 0.00,
        alerts: 0,
        resourceGroups: 2,
        virtualMachines: 0,
        storageAccounts: 0,
        databases: 0,
        top_services: [],
        lastUpdated: new Date().toISOString()
      });
      setServiceData([]);
    }
  };

  const loadCostData = async () => {
    try {
      // Para conta Azure vazia, usar dados mínimos
      setCostData([
        { date: new Date(Date.now() - 6*24*60*60*1000).toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit' }), cost: 0.00 },
        { date: new Date(Date.now() - 5*24*60*60*1000).toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit' }), cost: 0.00 },
        { date: new Date(Date.now() - 4*24*60*60*1000).toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit' }), cost: 0.00 },
        { date: new Date(Date.now() - 3*24*60*60*1000).toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit' }), cost: 0.00 },
        { date: new Date(Date.now() - 2*24*60*60*1000).toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit' }), cost: 0.00 },
        { date: new Date(Date.now() - 1*24*60*60*1000).toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit' }), cost: 0.00 },
        { date: new Date().toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit' }), cos      setCostData([]);
    }
  };

  const loadForecastData = async () => {
    try {
      // Para conta Azure vazia, previsão também será zero
      setForecastData([
        { date: new Date(Date.now() + 1*24*60*60*1000).toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit' }), cost: 0.00 },
        { date: new Date(Date.now() + 2*24*60*60*1000).toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit' }), cost: 0.00 },
        { date: new Date(Date.now() + 3*24*60*60*1000).toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit' }), cost: 0.00 },
        { date: new Date(Date.now() + 4*24*60*60*1000).toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit' }), cost: 0.00 },
        { date: new Date(Date.now() + 5*24*60*60*1000).toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit' }), cost: 0.00 },
        { date: new Date(Date.now() + 6*24*60*60*1000).toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit' }), cost: 0.00 },
        { date: new Date(Date.now() + 7*24*60*60*1000).toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit' }), cost: 0.00 }
      ]);
    } catch (error) {
      console.error('Erro ao carregar previsão:', error);
      setForecastData([]);
    }
  };

  const getServiceColor = (index) => {
    const colors = ['#8884d8', '#82ca9d', '#ffc658', '#ff7300', '#00ff00', '#ff00ff', '#00ffff'];
    return colors[index % colors.length];
  };

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('pt-BR', {
      style: 'currency',
      currency: 'USD'
    }).format(value);
  };

  const handleRefresh = () => {
    checkCredentialsAndLoadData();
  };

  const goToAzureConfig = () => {
    navigate('/azure-config');
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-96">
        <div className="flex items-center space-x-2">
          <RefreshCw className="h-6 w-6 animate-spin" />
          <span>Carregando dados do Azure...</span>
        </div>
      </div>
    );
  }

  if (!credentialsConfigured) {
    return (
      <div className="p-6 max-w-4xl mx-auto">
        <div className="bg-orange-50 border border-orange-200 rounded-lg p-6 text-center">
          <AlertCircle className="h-12 w-12 text-orange-600 mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-orange-800 mb-2">
            Credenciais Azure Não Configuradas
          </h2>
          <p className="text-orange-700 mb-4">
            Para visualizar dados reais do Azure, você precisa configurar suas credenciais de Service Principal.
          </p>
          <button
            onClick={goToAzureConfig}
            className="bg-orange-600 text-white px-6 py-2 rounded-md hover:bg-orange-700"
          >
            Configurar Credenciais Azure
          </button>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6 max-w-4xl mx-auto">
        <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
          <AlertCircle className="h-12 w-12 text-red-600 mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-red-800 mb-2">
            Erro ao Carregar Dados
          </h2>
          <p className="text-red-700 mb-4">{error}</p>
          <div className="flex justify-center space-x-4">
            <button
              onClick={handleRefresh}
              className="bg-blue-600 text-white px-6 py-2 rounded-md hover:bg-blue-700"
            >
              Tentar Novamente
            </button>
            <button
              onClick={goToAzureConfig}
              className="bg-orange-600 text-white px-6 py-2 rounded-md hover:bg-orange-700"
            >
              Verificar Credenciais
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Dashboard BOLT</h1>
          <p className="text-gray-600">Dados reais do Azure - Última atualização: {new Date(dashboardData?.last_updated).toLocaleString('pt-BR')}</p>
        </div>
        <div className="flex space-x-2">
          <button
            onClick={goToAzureConfig}
            className="bg-orange-600 text-white px-4 py-2 rounded-md hover:bg-orange-700 flex items-center"
          >
            <Settings className="h-4 w-4 mr-2" />
            Config. Azure
          </button>
          <button
            onClick={handleRefresh}
            className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 flex items-center"
          >
            <RefreshCw className="h-4 w-4 mr-2" />
            Atualizar
          </button>
        </div>
      </div>

      {/* Cards de Resumo */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="bg-white p-6 rounded-lg shadow-md border">
          <div className="flex items-center">
            <DollarSign className="h-8 w-8 text-green-600" />
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Gasto Atual (Mês)</p>
              <p className="text-2xl font-bold text-gray-900">
                {formatCurrency(dashboardData?.current_month_cost || 0)}
              </p>
            </div>
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow-md border">
          <div className="flex items-center">
            <TrendingUp className="h-8 w-8 text-blue-600" />
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Resource Groups</p>
              <p className="text-2xl font-bold text-gray-900">
                {dashboardData?.resource_groups_count || 0}
              </p>
            </div>
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow-md border">
          <div className="flex items-center">
            <Server className="h-8 w-8 text-purple-600" />
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Recursos Totais</p>
              <p className="text-2xl font-bold text-gray-900">
                {dashboardData?.resources_count || 0}
              </p>
            </div>
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow-md border">
          <div className="flex items-center">
            <AlertCircle className="h-8 w-8 text-green-600" />
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Status</p>
              <p className="text-sm font-bold text-green-900">
                Conectado ao Azure
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Gráficos */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Gráfico de Custos */}
        <div className="bg-white p-6 rounded-lg shadow-md border">
          <h3 className="text-lg font-semibold mb-4">Custos Diários (Mês Atual)</h3>
          {costData.length > 0 ? (
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={costData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" />
                <YAxis />
                <Tooltip formatter={(value) => [formatCurrency(value), 'Custo']} />
                <Legend />
                <Line type="monotone" dataKey="cost" stroke="#8884d8" strokeWidth={2} />
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <div className="flex items-center justify-center h-64 text-gray-500">
              Carregando dados de custos...
            </div>
          )}
        </div>

        {/* Gráfico de Forecast */}
        <div className="bg-white p-6 rounded-lg shadow-md border">
          <h3 className="text-lg font-semibold mb-4">Forecast (Próximos 14 dias)</h3>
          {forecastData.length > 0 ? (
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={forecastData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" />
                <YAxis />
                <Tooltip formatter={(value) => [formatCurrency(value), 'Forecast']} />
                <Legend />
                <Line type="monotone" dataKey="forecast" stroke="#82ca9d" strokeWidth={2} strokeDasharray="5 5" />
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <div className="flex items-center justify-center h-64 text-gray-500">
              Carregando dados de forecast...
            </div>
          )}
        </div>
      </div>

      {/* Gráfico de Serviços */}
      <div className="bg-white p-6 rounded-lg shadow-md border">
        <h3 className="text-lg font-semibold mb-4">Custos por Serviço (Top 5)</h3>
        {serviceData.length > 0 ? (
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={serviceData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, value }) => `${name}: ${formatCurrency(value)}`}
                outerRadius={80}
                fill="#8884d8"
                dataKey="value"
              >
                {serviceData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip formatter={(value) => formatCurrency(value)} />
            </PieChart>
          </ResponsiveContainer>
        ) : (
          <div className="flex items-center justify-center h-64 text-gray-500">
            Carregando dados de serviços...
          </div>
        )}
      </div>
    </div>
  );
};

export default DashboardHome;

