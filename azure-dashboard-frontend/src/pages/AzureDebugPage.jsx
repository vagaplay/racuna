import React, { useState } from 'react';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

const AzureDebugPage = () => {
  const [credentials, setCredentials] = useState({
    tenant_id: '',
    client_id: '',
    client_secret: '',
    subscription_id: ''
  });

  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setCredentials(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const testCredentials = async () => {
    setLoading(true);
    setResult(null);

    try {
      const response = await fetch(`${API_BASE_URL}/api/public/test-credentials-public`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(credentials)
      });

      const data = await response.json();
      setResult(data);
    } catch (error) {
      setResult({
        success: false,
        error: 'Erro de conexão',
        details: error.message
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ padding: '20px', maxWidth: '800px', margin: '0 auto' }}>
      <h1>🔧 Debug - Credenciais Azure</h1>
      <p>Teste suas credenciais de Service Principal</p>

      <div style={{ background: 'white', padding: '20px', borderRadius: '8px', marginBottom: '20px' }}>
        <h2>Credenciais</h2>
        
        <div style={{ marginBottom: '15px' }}>
          <label>Tenant ID:</label>
          <input
            type="text"
            name="tenant_id"
            value={credentials.tenant_id}
            onChange={handleInputChange}
            style={{ width: '100%', padding: '8px', marginTop: '5px' }}
          />
        </div>

        <div style={{ marginBottom: '15px' }}>
          <label>Client ID:</label>
          <input
            type="text"
            name="client_id"
            value={credentials.client_id}
            onChange={handleInputChange}
            style={{ width: '100%', padding: '8px', marginTop: '5px' }}
          />
        </div>

        <div style={{ marginBottom: '15px' }}>
          <label>Client Secret:</label>
          <input
            type="password"
            name="client_secret"
            value={credentials.client_secret}
            onChange={handleInputChange}
            style={{ width: '100%', padding: '8px', marginTop: '5px' }}
          />
        </div>

        <div style={{ marginBottom: '15px' }}>
          <label>Subscription ID:</label>
          <input
            type="text"
            name="subscription_id"
            value={credentials.subscription_id}
            onChange={handleInputChange}
            placeholder="Digite o Subscription ID"
            style={{ width: '100%', padding: '8px', marginTop: '5px' }}
          />
        </div>

        <button
          onClick={testCredentials}
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
          {loading ? 'Testando...' : '🧪 Testar Credenciais'}
        </button>
      </div>

      {result && (
        <div style={{
          background: result.success ? '#d4edda' : '#f8d7da',
          color: result.success ? '#155724' : '#721c24',
          padding: '15px',
          borderRadius: '8px',
          border: `1px solid ${result.success ? '#c3e6cb' : '#f5c6cb'}`
        }}>
          <h3>{result.success ? '✅ Sucesso!' : '❌ Erro'}</h3>
          
          {result.success ? (
            <div>
              <p><strong>Subscription:</strong> {result.subscription_name}</p>
              <p><strong>Subscription ID:</strong> {result.subscription_id}</p>
              <p><strong>Tenant ID:</strong> {result.tenant_id}</p>
            </div>
          ) : (
            <div>
              <p><strong>Erro:</strong> {result.error}</p>
              {result.details && (
                <details>
                  <summary>Detalhes técnicos</summary>
                  <pre style={{ background: '#f8f9fa', padding: '10px', marginTop: '10px' }}>
                    {result.details}
                  </pre>
                </details>
              )}
            </div>
          )}
        </div>
      )}

      <div style={{ background: '#f8f9fa', padding: '15px', borderRadius: '8px', marginTop: '20px' }}>
        <h3>💡 Dicas</h3>
        <ul>
          <li>Use as mesmas credenciais que funcionam no Azure CLI</li>
          <li>Verifique se o Service Principal tem permissões na subscription</li>
          <li>Certifique-se de que o Subscription ID está correto</li>
        </ul>
      </div>
    </div>
  );
};

export default AzureDebugPage;

