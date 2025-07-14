import React, { useState, useEffect } from 'react';
import { DollarSign, TrendingUp, AlertTriangle, Calendar, Target } from 'lucide-react';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

const BudgetPage = () => {
  const [budgetData, setBudgetData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    loadBudgetData();
  }, []);

  const loadBudgetData = async () => {
    try {
      setLoading(true);
      // Simular dados de orçamento por enquanto
      setTimeout(() => {
        setBudgetData({
          currentSpend: 150.75,
          budgetLimit: 200.00,
          currency: 'USD',
          period: 'Mensal',
          daysRemaining: 15,
          forecastedSpend: 185.50,
          alerts: [
            { type: 'warning', message: 'Você está próximo de 75% do seu orçamento' },
            { type: 'info', message: 'Previsão indica que você ficará dentro do orçamento' }
          ]
        });
        setLoading(false);
      }, 1000);
    } catch (error) {
      setError('Erro ao carregar dados de orçamento');
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-lg">Carregando dados de orçamento...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <div className="flex items-center">
          <AlertTriangle className="h-5 w-5 text-red-500 mr-2" />
          <span className="text-red-700">{error}</span>
        </div>
      </div>
    );
  }

  const usagePercentage = (budgetData.currentSpend / budgetData.budgetLimit) * 100;
  const forecastPercentage = (budgetData.forecastedSpend / budgetData.budgetLimit) * 100;

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold text-gray-900">Orçamento Azure</h1>
        <button 
          onClick={loadBudgetData}
          className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
        >
          <TrendingUp className="h-4 w-4 mr-2" />
          Atualizar
        </button>
      </div>

      {/* Cards de Resumo */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <DollarSign className="h-8 w-8 text-green-600" />
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Gasto Atual</p>
              <p className="text-2xl font-bold text-gray-900">
                ${budgetData.currentSpend.toFixed(2)}
              </p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <Target className="h-8 w-8 text-blue-600" />
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Limite do Orçamento</p>
              <p className="text-2xl font-bold text-gray-900">
                ${budgetData.budgetLimit.toFixed(2)}
              </p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <TrendingUp className="h-8 w-8 text-orange-600" />
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Previsão</p>
              <p className="text-2xl font-bold text-gray-900">
                ${budgetData.forecastedSpend.toFixed(2)}
              </p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <Calendar className="h-8 w-8 text-purple-600" />
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Dias Restantes</p>
              <p className="text-2xl font-bold text-gray-900">
                {budgetData.daysRemaining}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Barra de Progresso */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold mb-4">Uso do Orçamento</h2>
        <div className="space-y-4">
          <div>
            <div className="flex justify-between text-sm text-gray-600 mb-1">
              <span>Gasto Atual ({usagePercentage.toFixed(1)}%)</span>
              <span>${budgetData.currentSpend} / ${budgetData.budgetLimit}</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-3">
              <div 
                className={`h-3 rounded-full ${usagePercentage > 90 ? 'bg-red-500' : usagePercentage > 75 ? 'bg-yellow-500' : 'bg-green-500'}`}
                style={{ width: `${Math.min(usagePercentage, 100)}%` }}
              ></div>
            </div>
          </div>
          
          <div>
            <div className="flex justify-between text-sm text-gray-600 mb-1">
              <span>Previsão ({forecastPercentage.toFixed(1)}%)</span>
              <span>${budgetData.forecastedSpend} / ${budgetData.budgetLimit}</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div 
                className="h-2 rounded-full bg-blue-400 opacity-70"
                style={{ width: `${Math.min(forecastPercentage, 100)}%` }}
              ></div>
            </div>
          </div>
        </div>
      </div>

      {/* Alertas */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold mb-4">Alertas e Notificações</h2>
        <div className="space-y-3">
          {budgetData.alerts.map((alert, index) => (
            <div 
              key={index}
              className={`p-4 rounded-lg border ${
                alert.type === 'warning' 
                  ? 'bg-yellow-50 border-yellow-200 text-yellow-800' 
                  : 'bg-blue-50 border-blue-200 text-blue-800'
              }`}
            >
              <div className="flex items-center">
                <AlertTriangle className={`h-5 w-5 mr-2 ${
                  alert.type === 'warning' ? 'text-yellow-600' : 'text-blue-600'
                }`} />
                <span>{alert.message}</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Configurações Rápidas */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold mb-4">Configurações de Orçamento</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <button className="p-4 border border-gray-300 rounded-lg hover:bg-gray-50 text-left">
            <h3 className="font-medium">Configurar Alertas</h3>
            <p className="text-sm text-gray-600">Defina quando receber notificações</p>
          </button>
          <button className="p-4 border border-gray-300 rounded-lg hover:bg-gray-50 text-left">
            <h3 className="font-medium">Ajustar Limite</h3>
            <p className="text-sm text-gray-600">Modifique o limite do orçamento</p>
          </button>
        </div>
      </div>
    </div>
  );
};

export default BudgetPage;

