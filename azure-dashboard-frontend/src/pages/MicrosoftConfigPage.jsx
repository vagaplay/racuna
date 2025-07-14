import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';

const MicrosoftConfigPage = () => {
  const [config, setConfig] = useState({
    client_id: '',
    client_secret: '',
    redirect_uri: ''
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const navigate = useNavigate();

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setConfig(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setSuccess('');

    try {
      const response = await fetch('/api/microsoft/config', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify(config),
      });

      const data = await response.json();

      if (data.success) {
        setSuccess('✅ Configuração OAuth atualizada com sucesso!');
        
        // Limpar formulário
        setConfig({
          client_id: '',
          client_secret: '',
          redirect_uri: ''
        });
      } else {
        setError(data.error || 'Erro ao configurar OAuth');
      }
    } catch (error) {
      setError('Erro de conexão com o servidor');
    } finally {
      setLoading(false);
    }
  };

  const goToDashboard = () => {
    navigate('/dashboard');
  };

  const generateRedirectUri = () => {
    const baseUrl = window.location.origin;
    const redirectUri = `${baseUrl}/api/microsoft/callback`;
    setConfig(prev => ({
      ...prev,
      redirect_uri: redirectUri
    }));
  };

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900">Configuração Microsoft OAuth</h1>
        <p className="text-gray-600 mt-2">
          Configure o OAuth para login com Microsoft Entra ID
        </p>
      </div>

      <div className="bg-white rounded-lg shadow-md border p-6">
        <h2 className="text-xl font-semibold mb-4">
          Configurar App Registration
        </h2>
        
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
          <h3 className="text-sm font-semibold text-blue-800 mb-2">
            Como configurar no Azure Portal:
          </h3>
          <ol className="text-blue-700 text-sm space-y-1">
            <li>1. Acesse Azure Portal → Azure Active Directory</li>
            <li>2. Vá em "App registrations" → "New registration"</li>
            <li>3. Nome: "BOLT Dashboard"</li>
            <li>4. Supported account types: "Accounts in any organizational directory and personal Microsoft accounts"</li>
            <li>5. Redirect URI: Web → Use o botão "Gerar" abaixo</li>
            <li>6. Após criar, anote "Application (client) ID"</li>
            <li>7. Em "Certificates & secrets" → "New client secret"</li>
            <li>8. Anote o valor do secret (só aparece uma vez!)</li>
            <li>9. Em "API permissions" → Adicionar: "User.Read" e "https://management.azure.com/user_impersonation"</li>
          </ol>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Application (Client) ID
            </label>
            <input
              type="text"
              name="client_id"
              value={config.client_id}
              onChange={handleInputChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Client Secret
            </label>
            <input
              type="password"
              name="client_secret"
              value={config.client_secret}
              onChange={handleInputChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Valor do client secret"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Redirect URI
            </label>
            <div className="flex space-x-2">
              <input
                type="url"
                name="redirect_uri"
                value={config.redirect_uri}
                onChange={handleInputChange}
                className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="https://seu-dominio.com/api/microsoft/callback"
                required
              />
              <button
                type="button"
                onClick={generateRedirectUri}
                className="bg-gray-600 text-white px-4 py-2 rounded-md hover:bg-gray-700"
              >
                Gerar
              </button>
            </div>
            <p className="text-xs text-gray-500 mt-1">
              Use o botão "Gerar" para criar automaticamente a URI correta
            </p>
          </div>

          <div className="flex space-x-4">
            <button
              type="submit"
              disabled={loading}
              className="bg-blue-600 text-white px-6 py-2 rounded-md hover:bg-blue-700 disabled:opacity-50 flex-1"
            >
              {loading ? 'Configurando...' : 'Salvar Configuração'}
            </button>
            
            <button
              type="button"
              onClick={goToDashboard}
              className="bg-gray-600 text-white px-6 py-2 rounded-md hover:bg-gray-700"
            >
              Voltar ao Dashboard
            </button>
          </div>
        </form>

        {/* Mensagens */}
        {error && (
          <div className="mt-4 bg-red-50 border border-red-200 rounded-lg p-4">
            <p className="text-red-700 text-sm whitespace-pre-line">{error}</p>
          </div>
        )}

        {success && (
          <div className="mt-4 bg-green-50 border border-green-200 rounded-lg p-4">
            <p className="text-green-700 text-sm whitespace-pre-line">{success}</p>
          </div>
        )}

        {/* Informações adicionais */}
        <div className="mt-6 bg-yellow-50 border border-yellow-200 rounded-lg p-4">
          <h3 className="text-sm font-semibold text-yellow-800 mb-2">
            ⚠️ Importante:
          </h3>
          <ul className="text-yellow-700 text-sm space-y-1">
            <li>• Esta configuração é necessária apenas uma vez</li>
            <li>• Após configurar, o botão "Entrar com Microsoft" funcionará</li>
            <li>• Os usuários poderão fazer login com suas contas Microsoft/Azure AD</li>
            <li>• As permissões Azure serão herdadas da conta do usuário</li>
          </ul>
        </div>
      </div>
    </div>
  );
};

export default MicrosoftConfigPage;

