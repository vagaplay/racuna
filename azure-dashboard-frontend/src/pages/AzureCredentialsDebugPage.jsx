import React, { useState } from 'react';

const AzureCredentialsDebugPage = () => {
  const [authStatus, setAuthStatus] = useState(null);
  const [credentialsTest, setCredentialsTest] = useState(null);
  const [loading, setLoading] = useState(false);

  const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000';

  const checkAuthStatus = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${API_BASE_URL}/api/auth/status`, {
        method: 'GET',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
        }
      });
      
      const data = await response.json();
      setAuthStatus({
        status: response.status,
        data: data,
        headers: Object.fromEntries(response.headers.entries())
      });
    } catch (error) {
      setAuthStatus({
        error: error.message,
        status: 'NETWORK_ERROR'
      });
    }
    setLoading(false);
  };

  const testCredentialsEndpoint = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${API_BASE_URL}/api/azure/credentials-status`, {
        method: 'GET',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
        }
      });
      
      const data = await response.json();
      setCredentialsTest({
        status: response.status,
        data: data,
        headers: Object.fromEntries(response.headers.entries())
      });
    } catch (error) {
      setCredentialsTest({
        error: error.message,
        status: 'NETWORK_ERROR'
      });
    }
    setLoading(false);
  };

  const testCredentialsPost = async () => {
    setLoading(true);
    try {
      const testData = {
        subscription_id: "test-subscription-id",
        client_id: "test-client-id", 
        client_secret: "test-client-secret",
        tenant_id: "test-tenant-id"
      };

      const response = await fetch(`${API_BASE_URL}/api/azure/credentials`, {
        method: 'POST',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(testData)
      });
      
      const data = await response.json();
      setCredentialsTest({
        status: response.status,
        data: data,
        headers: Object.fromEntries(response.headers.entries()),
        requestData: testData
      });
    } catch (error) {
      setCredentialsTest({
        error: error.message,
        status: 'NETWORK_ERROR'
      });
    }
    setLoading(false);
  };

  const doLogin = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${API_BASE_URL}/api/auth/login`, {
        method: 'POST',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          email: 'test@test.com',
          password: '123456'
        })
      });
      
      const data = await response.json();
      setAuthStatus({
        status: response.status,
        data: data,
        headers: Object.fromEntries(response.headers.entries()),
        action: 'LOGIN'
      });
    } catch (error) {
      setAuthStatus({
        error: error.message,
        status: 'NETWORK_ERROR',
        action: 'LOGIN'
      });
    }
    setLoading(false);
  };

  return (
    <div className="p-6 max-w-6xl mx-auto">
      <h1 className="text-3xl font-bold mb-6">🔧 Debug - Credenciais Azure</h1>
      
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        
        {/* Seção de Autenticação */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold mb-4">🔐 Status de Autenticação</h2>
          
          <div className="space-y-3 mb-4">
            <button 
              onClick={doLogin}
              disabled={loading}
              className="w-full bg-green-600 text-white px-4 py-2 rounded hover:bg-green-700 disabled:opacity-50"
            >
              🔑 Fazer Login (test@test.com)
            </button>
            
            <button 
              onClick={checkAuthStatus}
              disabled={loading}
              className="w-full bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 disabled:opacity-50"
            >
              🔄 Verificar Status de Auth
            </button>
          </div>

          {authStatus && (
            <div className="mt-4">
              <h3 className="font-semibold mb-2">
                {authStatus.status === 200 ? '✅' : '❌'} Resultado Auth:
              </h3>
              <pre className="bg-gray-100 p-3 rounded text-sm overflow-auto max-h-64">
                {JSON.stringify(authStatus, null, 2)}
              </pre>
            </div>
          )}
        </div>

        {/* Seção de Credenciais */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold mb-4">🔧 Teste de Credenciais</h2>
          
          <div className="space-y-3 mb-4">
            <button 
              onClick={testCredentialsEndpoint}
              disabled={loading}
              className="w-full bg-orange-600 text-white px-4 py-2 rounded hover:bg-orange-700 disabled:opacity-50"
            >
              📊 GET /api/azure/credentials-status
            </button>
            
            <button 
              onClick={testCredentialsPost}
              disabled={loading}
              className="w-full bg-purple-600 text-white px-4 py-2 rounded hover:bg-purple-700 disabled:opacity-50"
            >
              📝 POST /api/azure/credentials (teste)
            </button>
          </div>

          {credentialsTest && (
            <div className="mt-4">
              <h3 className="font-semibold mb-2">
                {credentialsTest.status === 200 ? '✅' : '❌'} Resultado Credenciais:
              </h3>
              <pre className="bg-gray-100 p-3 rounded text-sm overflow-auto max-h-64">
                {JSON.stringify(credentialsTest, null, 2)}
              </pre>
            </div>
          )}
        </div>
      </div>

      {/* Informações de Debug */}
      <div className="mt-6 bg-yellow-50 border border-yellow-200 rounded-lg p-4">
        <h3 className="font-semibold text-yellow-800 mb-2">💡 Como usar este debug:</h3>
        <ol className="list-decimal list-inside text-yellow-700 space-y-1">
          <li>Primeiro clique em "🔑 Fazer Login" para autenticar</li>
          <li>Depois clique em "🔄 Verificar Status de Auth" para confirmar</li>
          <li>Se autenticado, teste "📊 GET credentials-status" para ver o erro</li>
          <li>Teste também "📝 POST credentials" para ver se aceita dados</li>
          <li>Copie qualquer erro que aparecer e me envie</li>
        </ol>
      </div>

      {/* Informações Técnicas */}
      <div className="mt-4 bg-gray-50 border border-gray-200 rounded-lg p-4">
        <h3 className="font-semibold text-gray-800 mb-2">🔧 Informações Técnicas:</h3>
        <div className="text-gray-600 text-sm space-y-1">
          <p><strong>API Base URL:</strong> {API_BASE_URL}</p>
          <p><strong>Cookies:</strong> {document.cookie || 'Nenhum cookie encontrado'}</p>
          <p><strong>User Agent:</strong> {navigator.userAgent}</p>
        </div>
      </div>
    </div>
  );
};

export default AzureCredentialsDebugPage;

