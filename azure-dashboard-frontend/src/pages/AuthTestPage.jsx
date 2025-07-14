import React, { useState, useEffect } from 'react';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

const AuthTestPage = () => {
  const [authStatus, setAuthStatus] = useState(null);
  const [loading, setLoading] = useState(false);

  const checkAuthStatus = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${API_BASE_URL}/api/auth/status`, {
        credentials: 'include'
      });
      const data = await response.json();
      setAuthStatus(data);
    } catch (error) {
      setAuthStatus({
        authenticated: false,
        error: error.message
      });
    } finally {
      setLoading(false);
    }
  };

  const testConfigureCredentials = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${API_BASE_URL}/api/azure/configure-credentials`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        credentials: 'include',
        body: JSON.stringify({
          tenant_id: '',
          client_id: '',
          client_secret: '',
          subscription_id: ''
        })
      });
      const data = await response.json();
      alert(JSON.stringify(data, null, 2));
    } catch (error) {
      alert('Erro: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  const testLogin = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${API_BASE_URL}/api/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        credentials: 'include',
        body: JSON.stringify({
          email: 'test@test.com',
          password: '123456'
        })
      });
      const data = await response.json();
      alert('Login result: ' + JSON.stringify(data, null, 2));
      
      // Verificar status após login
      setTimeout(() => {
        checkAuthStatus();
      }, 1000);
    } catch (error) {
      alert('Erro no login: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    checkAuthStatus();
  }, []);

  return (
    <div style={{ padding: '20px', maxWidth: '800px', margin: '0 auto' }}>
      <h1>🔐 Teste de Autenticação</h1>
      
      <div style={{ background: 'white', padding: '20px', borderRadius: '8px', marginBottom: '20px' }}>
        <h2>Status de Autenticação</h2>
        <div style={{ display: 'flex', gap: '10px', marginBottom: '15px' }}>
          <button onClick={checkAuthStatus} disabled={loading}>
            {loading ? 'Verificando...' : '🔄 Verificar Status'}
          </button>
          <button 
            onClick={testLogin} 
            disabled={loading}
            style={{
              background: '#28a745',
              color: 'white',
              padding: '8px 16px',
              border: 'none',
              borderRadius: '4px',
              cursor: loading ? 'not-allowed' : 'pointer'
            }}
          >
            {loading ? 'Fazendo login...' : '🔑 Fazer Login (test@test.com)'}
          </button>
        </div>
        
        {authStatus && (
          <div style={{
            marginTop: '15px',
            padding: '15px',
            background: authStatus.authenticated ? '#d4edda' : '#f8d7da',
            color: authStatus.authenticated ? '#155724' : '#721c24',
            borderRadius: '4px'
          }}>
            <h3>{authStatus.authenticated ? '✅ Autenticado' : '❌ Não Autenticado'}</h3>
            <pre>{JSON.stringify(authStatus, null, 2)}</pre>
          </div>
        )}
      </div>

      <div style={{ background: 'white', padding: '20px', borderRadius: '8px' }}>
        <h2>Teste de Configuração Azure</h2>
        <p>Este botão testa se você consegue configurar credenciais Azure (requer autenticação)</p>
        <button 
          onClick={testConfigureCredentials} 
          disabled={loading}
          style={{
            background: '#007bff',
            color: 'white',
            padding: '10px 20px',
            border: 'none',
            borderRadius: '4px',
            cursor: loading ? 'not-allowed' : 'pointer'
          }}
        >
          {loading ? 'Testando...' : '🧪 Testar Configure Credentials'}
        </button>
      </div>

      <div style={{ background: '#f8f9fa', padding: '15px', borderRadius: '8px', marginTop: '20px' }}>
        <h3>💡 Como usar:</h3>
        <ol>
          <li>Primeiro faça login na página principal</li>
          <li>Depois volte aqui e clique "🔄 Verificar Status"</li>
          <li>Se estiver autenticado, teste "🧪 Testar Configure Credentials"</li>
        </ol>
      </div>
    </div>
  );
};

export default AuthTestPage;

