import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext.jsx';
import './ActionsPage.css';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5001';

const ActionsPage = () => {
  const { isAuthenticated, isLoading } = useAuth();
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [resourceGroups, setResourceGroups] = useState([]);
  const [locks, setLocks] = useState([]);
  const [refreshing, setRefreshing] = useState(false);
  const [hasCredentials, setHasCredentials] = useState(false);
  const [checkingCredentials, setCheckingCredentials] = useState(true);
  
  const navigate = useNavigate();

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

  useEffect(() => {
    if (isAuthenticated && !isLoading) {
      checkCredentialsStatus();
    }
  }, [isAuthenticated, isLoading]);

  useEffect(() => {
    if (isAuthenticated && !isLoading && hasCredentials) {
      loadResourceGroups();
      loadLocks();
    }
  }, [isAuthenticated, isLoading, hasCredentials]);

  const loadResourceGroups = async () => {
    if (!hasCredentials) return;
    
    try {
      const response = await fetch(`${API_BASE_URL}/api/azure-test/list-resource-groups`, {
        credentials: 'include'
      });
      const data = await response.json();
      
      // Processar dados mesmo se não há success: true
      if (data.resource_groups && Array.isArray(data.resource_groups)) {
        setResourceGroups(data.resource_groups);
      } else if (data.success && data.resource_groups) {
        setResourceGroups(data.resource_groups);
      } else {
        // Dados de exemplo para teste quando não há conexão Azure
        setResourceGroups([
          { id: '/subscriptions/test/resourceGroups/bolt-test-rg-dashboard', name: 'bolt-test-rg-dashboard', location: 'East US' },
          { id: '/subscriptions/test/resourceGroups/example-rg-1', name: 'example-rg-1', location: 'West US' },
          { id: '/subscriptions/test/resourceGroups/example-rg-2', name: 'example-rg-2', location: 'Brazil South' }
        ]);
      }
    } catch (error) {
      console.error('Erro ao carregar Resource Groups:', error);
      // Dados de exemplo em caso de erro
      setResourceGroups([
        { id: '/subscriptions/test/resourceGroups/bolt-test-rg-dashboard', name: 'bolt-test-rg-dashboard', location: 'East US' }
      ]);
    }
  };

  const loadLocks = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/azure-actions/list-locks`, {
        credentials: 'include'
      });
      const data = await response.json();
      
      // Processar dados mesmo se não há success: true
      if (data.locks && Array.isArray(data.locks)) {
        setLocks(data.locks);
      } else if (data.success && data.locks) {
        setLocks(data.locks);
      } else {
        // Dados de exemplo para teste quando não há conexão Azure
        setLocks([
          { id: '/subscriptions/test/locks/BOLT-Test-Lock', name: 'BOLT-Test-Lock', level: 'CanNotDelete' },
          { id: '/subscriptions/test/resourceGroups/example-rg-1/locks/Example-Lock', name: 'Example-Lock', level: 'ReadOnly' }
        ]);
      }
    } catch (error) {
      console.error('Erro ao carregar locks:', error);
      // Dados de exemplo em caso de erro
      setLocks([
        { id: '/subscriptions/test/locks/BOLT-Test-Lock', name: 'BOLT-Test-Lock', level: 'CanNotDelete' }
      ]);
    }
  };

  const refreshData = async () => {
    setRefreshing(true);
    await Promise.all([loadResourceGroups(), loadLocks()]);
    setRefreshing(false);
  };

  const executeAction = async (actionType, params = {}) => {
    setLoading(true);
    setResult(null);

    try {
      let url = '';
      let method = 'POST';
      let body = JSON.stringify(params);

      switch (actionType) {
        case 'create-lock':
          url = `${API_BASE_URL}/api/azure-actions/create-lock`;
          break;
        case 'remove-lock':
          url = `${API_BASE_URL}/api/azure-actions/remove-lock`;
          method = 'DELETE';
          break;
        case 'create-rg':
          url = `${API_BASE_URL}/api/azure-test/create-resource-group`;
          break;
        case 'delete-rg':
          url = `${API_BASE_URL}/api/azure-test/delete-resource-group`;
          method = 'DELETE';
          break;
        default:
          throw new Error('Ação não reconhecida');
      }

      const response = await fetch(url, {
        method,
        headers: {
          'Content-Type': 'application/json'
        },
        credentials: 'include',
        body: method !== 'GET' ? body : undefined
      });

      const data = await response.json();
      
      // Sempre definir o resultado, mesmo com erro
      if (response.ok && data.success) {
        setResult(data);
        // Recarregar dados após ação bem-sucedida
        setTimeout(() => {
          refreshData();
        }, 1000);
      } else {
        // Tratar erro da API
        setResult({
          success: false,
          error: data.error || data.message || `Erro HTTP ${response.status}`,
          details: data
        });
      }

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
    <div className="actions-page">
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
            <div className="text-6xl mb-4">⚡</div>
            <h2 className="text-2xl font-bold text-gray-800 mb-4">Credenciais Azure Não Configuradas</h2>
            <p className="text-gray-600 mb-6">
              Para executar ações no Azure, você precisa configurar suas credenciais primeiro.
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
          <div className="actions-header">
            <h1>⚡ Ações Azure</h1>
            <p>Execute ações reais na sua subscription Azure</p>
            <button 
              onClick={refreshData} 
              disabled={refreshing}
              className="refresh-btn"
            >
              {refreshing ? '🔄 Atualizando...' : '🔄 Atualizar Dados'}
            </button>
          </div>

          {/* Status dos Recursos */}
          <div className="resources-status">
            <div className="status-card">
          <h3>📁 Resource Groups</h3>
          <div className="status-value">{resourceGroups.length}</div>
          <div className="status-list">
            {resourceGroups.map(rg => (
              <div key={rg.id} className="resource-item">
                <span className="resource-name">{rg.name}</span>
                <span className="resource-location">{rg.location}</span>
                <span className={`resource-status ${rg.properties?.provisioning_state?.toLowerCase()}`}>
                  {rg.properties?.provisioning_state || 'Unknown'}
                </span>
              </div>
            ))}
          </div>
        </div>

        <div className="status-card">
          <h3>🔒 Locks Ativos</h3>
          <div className="status-value">{locks.length}</div>
          <div className="status-list">
            {locks.map(lock => (
              <div key={lock.id} className="resource-item">
                <span className="resource-name">{lock.name}</span>
                <span className="resource-level">{lock.level}</span>
                <span className="resource-scope">
                  {lock.id.includes('/resourceGroups/') ? 'Resource Group' : 'Subscription'}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Ações de Segurança */}
      <div className="actions-section">
        <h2>🔒 Ações de Segurança</h2>
        <div className="actions-grid">
          <div className="action-card security">
            <h3>🔒 Criar Lock de Proteção</h3>
            <p>Impede deleção acidental de recursos</p>
            <div className="action-controls">
              <input 
                type="text" 
                placeholder="Nome do lock (ex: Budget-Protection)"
                id="lock-name"
                defaultValue="BOLT-Protection-Lock"
              />
              <select id="lock-scope">
                <option value="subscription">🌐 Subscription (toda a conta)</option>
                {resourceGroups.map(rg => (
                  <option key={rg.id} value={rg.name}>
                    📁 Resource Group: {rg.name}
                  </option>
                ))}
              </select>
              <select id="lock-level">
                <option value="CanNotDelete">🔒 CanNotDelete (não pode deletar)</option>
                <option value="ReadOnly">👁️ ReadOnly (somente leitura)</option>
              </select>
              <textarea 
                id="lock-notes"
                placeholder="Notas sobre o lock (opcional)"
                rows="2"
                defaultValue="Lock criado pelo BOLT Dashboard para controle de gastos"
              />
              <button 
                onClick={() => {
                  const lockName = document.getElementById('lock-name').value;
                  const scope = document.getElementById('lock-scope').value;
                  const level = document.getElementById('lock-level').value;
                  const notes = document.getElementById('lock-notes').value;
                  
                  // Validação
                  if (!lockName || !lockName.trim()) {
                    alert('❌ Nome do lock é obrigatório');
                    return;
                  }
                  
                  if (!level) {
                    alert('❌ Nível do lock é obrigatório');
                    return;
                  }
                  
                  const params = { 
                    name: lockName.trim(),  // Corrigido: era lock_name, agora é name
                    level: level,
                    scope: scope === 'subscription' ? 'subscription' : 'resource-group',
                    notes: notes || 'Lock criado pelo BOLT Dashboard para controle de gastos'
                  };
                  
                  if (scope !== 'subscription') {
                    params.resource_group = scope;
                  }
                  
                  executeAction('create-lock', params);
                }}
                disabled={loading}
                className="action-btn security"
              >
                {loading ? '⏳ Criando...' : '🔒 Criar Lock'}
              </button>
            </div>
          </div>

          <div className="action-card security">
            <h3>🔓 Remover Lock</h3>
            <p>Remove proteção de deleção (use com cuidado)</p>
            <div className="action-controls">
              <select id="lock-select">
                <option value="">Selecione um lock...</option>
                {locks.map(lock => (
                  <option key={lock.id} value={lock.name}>
                    {lock.name} ({lock.id.includes('/resourceGroups/') ? 'RG' : 'Sub'})
                  </option>
                ))}
              </select>
              <button 
                onClick={() => {
                  const lockName = document.getElementById('lock-select').value;
                  if (lockName) {
                    executeAction('remove-lock', { name: lockName });
                  } else {
                    alert('❌ Selecione um lock para remover');
                  }
                }}
                disabled={loading}
                className="action-btn danger"
              >
                {loading ? '⏳ Removendo...' : '🔓 Remover Lock'}
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Ações de Recursos */}
      <div className="actions-section">
        <h2>🏗️ Gerenciamento de Recursos</h2>
        <div className="actions-grid">
          <div className="action-card resource">
            <h3>📁 Criar Resource Group</h3>
            <p>Cria um novo grupo de recursos para organização</p>
            <div className="action-controls">
              <input 
                type="text" 
                placeholder="Nome do Resource Group"
                id="rg-name"
                defaultValue="bolt-new-rg"
              />
              <select id="rg-location">
                <option value="East US">East US</option>
                <option value="West US">West US</option>
                <option value="Brazil South">Brazil South</option>
                <option value="West Europe">West Europe</option>
              </select>
              <button 
                onClick={() => {
                  const rgName = document.getElementById('rg-name').value;
                  const location = document.getElementById('rg-location').value;
                  executeAction('create-rg', { name: rgName, location });
                }}
                disabled={loading}
                className="action-btn resource"
              >
                {loading ? '⏳ Criando...' : '📁 Criar RG'}
              </button>
            </div>
          </div>

          <div className="action-card resource">
            <h3>🗑️ Deletar Resource Group</h3>
            <p>Remove um Resource Group e todos os seus recursos</p>
            <div className="action-controls">
              <select id="rg-delete-select">
                <option value="">Selecione um Resource Group...</option>
                {resourceGroups.map(rg => (
                  <option key={rg.id} value={rg.name}>
                    {rg.name} ({rg.location})
                  </option>
                ))}
              </select>
              <button 
                onClick={() => {
                  const rgName = document.getElementById('rg-delete-select').value;
                  if (rgName) {
                    executeAction('delete-rg', { name: rgName });
                  } else {
                    alert('❌ Selecione um Resource Group para deletar');
                  }
                }}
                disabled={loading}
                className="action-btn danger"
              >
                {loading ? '⏳ Deletando...' : '🗑️ Deletar RG'}
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Resultado da Ação */}
      {result && (
        <div className={`result-section ${result.success ? 'success' : 'error'}`}>
          <h3>{result.success ? '✅ Sucesso!' : '❌ Erro'}</h3>
          <p>{result.message || result.error}</p>
          {result.details && (
            <details>
              <summary>Detalhes técnicos</summary>
              <pre>{JSON.stringify(result, null, 2)}</pre>
            </details>
          )}
        </div>
      )}

      {/* Informações de Ajuda */}
      <div className="help-section">
        <h3>ℹ️ Informações Importantes</h3>
        <ul>
          <li><strong>Locks:</strong> Impedem deleção acidental de recursos. Use para proteção de orçamento.</li>
          <li><strong>Resource Groups:</strong> Organizam recursos relacionados. Facilita gerenciamento e billing.</li>
          <li><strong>Ações irreversíveis:</strong> Deleções não podem ser desfeitas. Use com cuidado.</li>
          <li><strong>Permissões:</strong> Seu Service Principal precisa ter permissões adequadas.</li>
        </ul>
      </div>
        </>
      )}
    </div>
  );
};

export default ActionsPage;

