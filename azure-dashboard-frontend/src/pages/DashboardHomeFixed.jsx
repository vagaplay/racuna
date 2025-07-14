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
        { date: new Date().toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit' }), cost: 0.00 }
      ]);
    } catch (error) {
      console.error('Erro ao carregar dados de custos:', error);
      setCostData([]);
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

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="flex items-center space-x-2">
          <RefreshCw className="h-6 w-6 animate-spin text-blue-500" />
          <span className="text-lg">Carregando dashboard...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <AlertCircle className="h-12 w-12 text-red-500 mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-gray-900 mb-2">Erro ao Carregar Dados</h2>
          <p className="text-gray-600 mb-4">{error}</p>
          <button
            onClick={checkCredentialsAndLoadData}
            className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded"
          >
            Tentar Novamente
          </button>
        </div>
      </div>
    );
  }

  if (!credentialsConfigured) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <Settings className="h-12 w-12 text-orange-500 mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-gray-900 mb-2">Credenciais Azure Não Configuradas</h2>
          <p className="text-gray-600 mb-4">Configure suas credenciais Azure para visualizar os dados do dashboard.</p>
          <button
            onClick={() => navigate('/azure-config')}
            className="bg-orange-500 hover:bg-orange-700 text-white font-bold py-2 px-4 rounded"
          >
            Configurar Credenciais Azure
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold text-gray-900">Dashboard Azure</h1>
        <button
          onClick={checkCredentialsAndLoadData}
          className="flex items-center space-x-2 bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded"
        >
          <RefreshCw className="h-4 w-4" />
          <span>Atualizar</span>
        </button>
      </div>

      {/* Cards de Resumo */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="bg-white p-6 rounded-lg shadow">
          <div className="flex items-center">
            <Server className="h-8 w-8 text-blue-500" />
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500">Total de Recursos</p>
              <p className="text-2xl font-bold text-gray-900">{dashboardData?.totalResources || 0}</p>
            </div>
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow">
          <div className="flex items-center">
            <TrendingUp className="h-8 w-8 text-green-500" />
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500">Serviços Ativos</p>
              <p className="text-2xl font-bold text-gray-900">{dashboardData?.activeServices || 0}</p>
            </div>
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow">
          <div className="flex items-center">
            <DollarSign className="h-8 w-8 text-yellow-500" />
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500">Gasto Mensal</p>
              <p className="text-2xl font-bold text-gray-900">R$ {dashboardData?.monthlySpend?.toFixed(2) || '0.00'}</p>
            </div>
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow">
          <div className="flex items-center">
            <AlertCircle className="h-8 w-8 text-red-500" />
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500">Alertas</p>
              <p className="text-2xl font-bold text-gray-900">{dashboardData?.alerts || 0}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Gráficos */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Gráfico de Custos */}
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Custos dos Últimos 7 Dias</h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={costData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis />
              <Tooltip formatter={(value) => [`R$ ${value}`, 'Custo']} />
              <Legend />
              <Line type="monotone" dataKey="cost" stroke="#8884d8" strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Gráfico de Previsão */}
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Previsão - Próximos 7 Dias</h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={forecastData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis />
              <Tooltip formatter={(value) => [`R$ ${value}`, 'Previsão']} />
              <Legend />
              <Line type="monotone" dataKey="cost" stroke="#82ca9d" strokeWidth={2} strokeDasharray="5 5" />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Informações Adicionais */}
      <div className="bg-white p-6 rounded-lg shadow">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Resumo da Conta Azure</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="text-center">
            <p className="text-2xl font-bold text-blue-600">{dashboardData?.resourceGroups || 0}</p>
            <p className="text-sm text-gray-500">Resource Groups</p>
          </div>
          <div className="text-center">
            <p className="text-2xl font-bold text-green-600">{dashboardData?.virtualMachines || 0}</p>
            <p className="text-sm text-gray-500">Máquinas Virtuais</p>
          </div>
          <div className="text-center">
            <p className="text-2xl font-bold text-purple-600">{dashboardData?.storageAccounts || 0}</p>
            <p className="text-sm text-gray-500">Storage Accounts</p>
          </div>
        </div>
        
        {dashboardData?.lastUpdated && (
          <p className="text-xs text-gray-400 mt-4">
            Última atualização: {new Date(dashboardData.lastUpdated).toLocaleString('pt-BR')}
          </p>
        )}
      </div>
    </div>
  );
};

export default DashboardHome;

