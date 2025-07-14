import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext.jsx';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5001';

const AzureConfigPage = () => {
  const { isAuthenticated, isLoading } = useAuth();
  const [credentials, setCredentials] = useState({
    tenant_id: '',
    client_id: '',
    client_secret: '',
    subscription_id: ''
  });
  const [isConfigured, setIsConfigured] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [subscriptionInfo, setSubscriptionInfo] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    if (isAuthenticated && !isLoading) {
      checkCredentialsStatus();
    }
  }, [isAuthenticated, isLoading]);

  const checkCredentialsStatus = async () => {
    try {
      console.log('Verificando status das credenciais...');
      const response = await fetch(`${API_BASE_URL}/api/azure/credentials-status`, {
        credentials: 'include'
      });
      
      if (response.ok) {
        const data = await response.json();
        console.log('Status das credenciais:', data);
        
        if (data.configured) {
          setIsConfigured(true);
          setSubscriptionInfo(data);
        } else {
          // Limpar estados quando credenciais não estão configuradas
          setIsConfigured(false);
          setSubscriptionInfo(null);
        }
      }
    } catch (error) {
      console.error('Erro ao verificar status das credenciais:', error);
    }
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setCredentials(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setSuccess('');

    // Validar campos obrigatórios
    if (!credentials.tenant_id || !credentials.client_id || !credentials.client_secret || !credentials.subscription_id) {
      setError('Todos os campos são obrigatórios');
      setLoading(false);
      return;
    }

    try {
      const response = await fetch(`${API_BASE_URL}/api/azure/configure-credentials`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify(credentials),
      });

      const data = await response.json();

      if (response.ok && data.success) {
        console.log('✅ Credenciais salvas com sucesso, iniciando atualização...');
        setSuccess(`✅ Credenciais configuradas com sucesso!\n\nSubscription: ${data.subscription_name}\nID: ${data.subscription_id}`);
        
        // Limpar formulário
        setCredentials({
          tenant_id: '',
          client_id: '',
          client_secret: '',
          subscription_id: ''
        });
        
        console.log('📝 Formulário limpo, forçando atualização do estado...');
        
        // Forçar atualização imediata do estado
        setIsConfigured(true);
        setSubscriptionInfo({
          subscription_id: data.subscription_id,
          subscription_name: data.subscription_name,
          tenant_id: credentials.tenant_id,
          client_id: credentials.client_id
        });
        
        // Também chamar checkCredentialsStatus como backup
        setTimeout(async () => {
          await checkCredentialsStatus();
          console.log('✅ checkCredentialsStatus concluído como backup');
        }, 1000);
      } else {
        setError(data.error || data.message || 'Erro ao configurar credenciais');
      }
    } catch (error) {
      console.error('Erro de conexão:', error);
      setError('Erro de conexão com o servidor. Verifique se o backend está rodando.');
    } finally {
      setLoading(false);
    }
  };

  const handleTestConnection = async () => {
    setLoading(true);
    setError('');
    setSuccess('');

    try {
      const response = await fetch(`${API_BASE_URL}/api/azure/test-connection`, {
        method: 'POST',
        credentials: 'include'
      });

      const data = await response.json();

      if (response.ok && data.success) {
        setSuccess(`✅ Conexão testada com sucesso!\n\nEncontrados ${data.resource_groups_count} resource groups.\n\nPrimeiros grupos:\n${data.resource_groups.map(rg => `• ${rg.name} (${rg.location})`).join('\n')}`);
      } else {
        setError(data.error || 'Erro ao testar conexão');
      }
    } catch (error) {
      console.error('Erro de conexão:', error);
      setError('Erro de conexão com o servidor');
    } finally {
      setLoading(false);
    }
  };

  const handleRemoveCredentials = async () => {
    // Removendo confirmação temporariamente para teste
    console.log('🗑️ Iniciando remoção de credenciais...');

    setLoading(true);
    setError('');
    setSuccess('');

    try {
      const response = await fetch(`${API_BASE_URL}/api/azure/remove-credentials`, {
        method: 'DELETE',
        credentials: 'include'
      });

      const data = await response.json();

      if (response.ok && data.success) {
        setSuccess('✅ Credenciais removidas com sucesso!');
        
        // Atualizar status das credenciais automaticamente
        await checkCredentialsStatus();
      } else {
        setError(data.error || 'Erro ao remover credenciais');
      }
    } catch (error) {
      console.error('Erro de conexão:', error);
      setError('Erro de conexão com o servidor');
    } finally {
      setLoading(false);
    }
  };

  const goToDashboard = () => {
    navigate('/dashboard');
  };

  // Mostrar loading se ainda está verificando autenticação
  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Carregando...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <div className="mb-6">
        <button
          onClick={goToDashboard}
          className="mb-4 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
        >
          ← Voltar ao Dashboard
        </button>
        <h1 className="text-3xl font-bold text-gray-900">Configuração Azure</h1>
        <p className="text-gray-600 mt-2">Configure suas credenciais do Azure para acessar os recursos</p>
      </div>

      {/* Status das Credenciais */}
      {isConfigured && subscriptionInfo && (
        <div className="mb-6 p-4 bg-green-50 border border-green-200 rounded-lg">
          <h2 className="text-lg font-semibold text-green-800 mb-2">✅ Credenciais Configuradas</h2>
          <p className="text-green-700">
            <strong>Subscription:</strong> {subscriptionInfo.subscription_name}<br/>
            <strong>ID:</strong> {subscriptionInfo.subscription_id}
          </p>
          <div className="mt-4 space-x-2">
            <button
              onClick={handleTestConnection}
              disabled={loading}
              className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
            >
              {loading ? 'Testando...' : 'Testar Conexão'}
            </button>
            <button
              onClick={handleRemoveCredentials}
              disabled={loading}
              className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700 disabled:opacity-50"
            >
              {loading ? 'Removendo...' : 'Remover Credenciais'}
            </button>
          </div>
        </div>
      )}

      {/* Formulário de Configuração */}
      <div className="bg-white shadow-md rounded-lg p-6">
        <h2 className="text-xl font-semibold mb-4">
          {isConfigured ? 'Atualizar Credenciais' : 'Configurar Credenciais Azure'}
        </h2>
        
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label htmlFor="tenant_id" className="block text-sm font-medium text-gray-700 mb-1">
              Tenant ID
            </label>
            <input
              type="text"
              id="tenant_id"
              name="tenant_id"
              value={credentials.tenant_id}
              onChange={handleInputChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Ex: 8245f66a-b3fa-4019-9bdd-746320d1855c"
              required
            />
          </div>

          <div>
            <label htmlFor="client_id" className="block text-sm font-medium text-gray-700 mb-1">
              Client ID
            </label>
            <input
              type="text"
              id="client_id"
              name="client_id"
              value={credentials.client_id}
              onChange={handleInputChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Ex: 7d49dfab-0f44-4972-9ef1-894de8918b41"
              required
            />
          </div>

          <div>
            <label htmlFor="client_secret" className="block text-sm font-medium text-gray-700 mb-1">
              Client Secret
            </label>
            <input
              type="password"
              id="client_secret"
              name="client_secret"
              value={credentials.client_secret}
              onChange={handleInputChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Ex: ~cP8Q~rx6pY9r4EOqmmMfeKdZKoTPtBatK02NaZF"
              required
            />
          </div>

          <div>
            <label htmlFor="subscription_id" className="block text-sm font-medium text-gray-700 mb-1">
              Subscription ID
            </label>
            <input
              type="text"
              id="subscription_id"
              name="subscription_id"
              value={credentials.subscription_id}
              onChange={handleInputChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Ex: d5da2aa9-040f-4924-ad21-97105d90a8bb"
              required
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:opacity-50"
          >
            {loading ? 'Configurando...' : 'Configurar Credenciais'}
          </button>
        </form>
      </div>

      {/* Mensagens de Erro e Sucesso */}
      {error && (
        <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg">
          <p className="text-red-800 whitespace-pre-line">{error}</p>
        </div>
      )}

      {success && (
        <div className="mt-4 p-4 bg-green-50 border border-green-200 rounded-lg">
          <p className="text-green-800 whitespace-pre-line">{success}</p>
        </div>
      )}
    </div>
  );
};

export default AzureConfigPage;

