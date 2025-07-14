import React, { useState, useEffect } from 'react';
import { Calendar, Clock, Play, Pause, Trash2, Plus, Settings, Activity } from 'lucide-react';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000';

const SchedulesUnifiedPage = () => {
  const [activeTab, setActiveTab] = useState('list');
  const [schedules, setSchedules] = useState([]);
  const [executions, setExecutions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showCreateForm, setShowCreateForm] = useState(false);

  // Estado do formulário
  const [formData, setFormData] = useState({
    name: '',
    type: 'vm_shutdown',
    frequency: 'daily',
    time: '22:00',
    days: [],
    scope: 'subscription',
    resource_group: '',
    tags: '',
    enabled: true,
    notifications: true,
    email: ''
  });

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      await Promise.all([
        loadSchedules(),
        loadExecutions()
      ]);
    } catch (err) {
      setError('Erro ao carregar dados: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  const loadSchedules = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/schedules/list`, {
        credentials: 'include'
      });
      if (response.ok) {
        const data = await response.json();
        setSchedules(data.schedules || []);
      } else if (response.status === 401) {
        setError('Usuário não autenticado. Faça login novamente.');
      }
    } catch (err) {
      console.error('Erro ao carregar agendamentos:', err);
    }
  };

  const loadExecutions = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/schedules/executions`, {
        credentials: 'include'
      });
      if (response.ok) {
        const data = await response.json();
        setExecutions(data.executions || []);
      }
    } catch (err) {
      console.error('Erro ao carregar execuções:', err);
    }
  };

  const handleCreateSchedule = async (e) => {
    e.preventDefault();
    try {
      const response = await fetch(`${API_BASE_URL}/api/schedules/create`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify(formData)
      });

      if (response.ok) {
        setShowCreateForm(false);
        setFormData({
          name: '',
          type: 'vm_shutdown',
          frequency: 'daily',
          time: '22:00',
          days: [],
          scope: 'subscription',
          resource_group: '',
          tags: '',
          enabled: true,
          notifications: true,
          email: ''
        });
        await loadSchedules();
      } else if (response.status === 401) {
        setError('Usuário não autenticado. Faça login novamente.');
      }
    } catch (err) {
      setError('Erro ao criar agendamento: ' + err.message);
    }
  };

  const toggleSchedule = async (scheduleId, enabled) => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/schedules/${scheduleId}/toggle`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({ enabled: !enabled })
      });

      if (response.ok) {
        await loadSchedules();
      }
    } catch (err) {
      console.error('Erro ao alterar agendamento:', err);
    }
  };

  const deleteSchedule = async (scheduleId) => {
    if (!confirm('Tem certeza que deseja excluir este agendamento?')) return;

    try {
      const response = await fetch(`${API_BASE_URL}/api/schedules/${scheduleId}`, {
        method: 'DELETE',
        credentials: 'include'
      });

      if (response.ok) {
        await loadSchedules();
      }
    } catch (err) {
      console.error('Erro ao excluir agendamento:', err);
    }
  };

  const getTypeLabel = (type) => {
    const types = {
      'vm_shutdown': 'Desligar VMs',
      'vm_startup': 'Ligar VMs',
      'backup': 'Backup',
      'cleanup': 'Limpeza',
      'report': 'Relatório',
      'security_scan': 'Scan de Segurança'
    };
    return types[type] || type;
  };

  const getFrequencyLabel = (frequency) => {
    const frequencies = {
      'daily': 'Diário',
      'weekly': 'Semanal',
      'monthly': 'Mensal'
    };
    return frequencies[frequency] || frequency;
  };

  const getStatusBadge = (enabled) => {
    return (
      <span className={`px-2 py-1 rounded-full text-xs font-medium ${
        enabled 
          ? 'bg-green-100 text-green-800' 
          : 'bg-gray-100 text-gray-800'
      }`}>
        {enabled ? 'Ativo' : 'Inativo'}
      </span>
    );
  };

  const getExecutionStatusBadge = (status) => {
    const statusConfig = {
      'success': { bg: 'bg-green-100', text: 'text-green-800', label: 'Sucesso' },
      'failed': { bg: 'bg-red-100', text: 'text-red-800', label: 'Falhou' },
      'running': { bg: 'bg-blue-100', text: 'text-blue-800', label: 'Executando' },
      'pending': { bg: 'bg-yellow-100', text: 'text-yellow-800', label: 'Pendente' }
    };
    const config = statusConfig[status] || statusConfig['pending'];
    
    return (
      <span className={`px-2 py-1 rounded-full text-xs font-medium ${config.bg} ${config.text}`}>
        {config.label}
      </span>
    );
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        <span className="ml-2">Carregando agendamentos...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-md p-4">
        <div className="flex">
          <div className="flex-shrink-0">
            <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
            </svg>
          </div>
          <div className="ml-3">
            <h3 className="text-sm font-medium text-red-800">Erro ao Carregar Dados</h3>
            <div className="mt-2 text-sm text-red-700">
              <p>{error}</p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Agendamentos</h1>
          <p className="text-gray-600">Gerencie automações e tarefas programadas</p>
        </div>
        <button
          onClick={() => setShowCreateForm(true)}
          className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md flex items-center gap-2"
        >
          <Plus className="h-4 w-4" />
          Novo Agendamento
        </button>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          <button
            onClick={() => setActiveTab('list')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'list'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            <Calendar className="h-4 w-4 inline mr-2" />
            Agendamentos
          </button>
          <button
            onClick={() => setActiveTab('executions')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'executions'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            <Activity className="h-4 w-4 inline mr-2" />
            Histórico de Execuções
          </button>
        </nav>
      </div>

      {/* Content */}
      {activeTab === 'list' && (
        <div className="space-y-4">
          {schedules.length === 0 ? (
            <div className="text-center py-12">
              <Calendar className="mx-auto h-12 w-12 text-gray-400" />
              <h3 className="mt-2 text-sm font-medium text-gray-900">Nenhum agendamento</h3>
              <p className="mt-1 text-sm text-gray-500">Comece criando seu primeiro agendamento.</p>
              <div className="mt-6">
                <button
                  onClick={() => setShowCreateForm(true)}
                  className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md"
                >
                  Criar Agendamento
                </button>
              </div>
            </div>
          ) : (
            <div className="grid gap-4">
              {schedules.map((schedule) => (
                <div key={schedule.id} className="bg-white border border-gray-200 rounded-lg p-6">
                  <div className="flex justify-between items-start">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2">
                        <h3 className="text-lg font-medium text-gray-900">{schedule.name}</h3>
                        {getStatusBadge(schedule.enabled)}
                      </div>
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm text-gray-600">
                        <div>
                          <span className="font-medium">Tipo:</span> {getTypeLabel(schedule.type)}
                        </div>
                        <div>
                          <span className="font-medium">Frequência:</span> {getFrequencyLabel(schedule.frequency)}
                        </div>
                        <div>
                          <span className="font-medium">Horário:</span> {schedule.time}
                        </div>
                        <div>
                          <span className="font-medium">Escopo:</span> {schedule.scope}
                        </div>
                      </div>
                      {schedule.next_execution && (
                        <div className="mt-2 text-sm text-gray-500">
                          <Clock className="h-4 w-4 inline mr-1" />
                          Próxima execução: {new Date(schedule.next_execution).toLocaleString('pt-BR')}
                        </div>
                      )}
                    </div>
                    <div className="flex items-center gap-2 ml-4">
                      <button
                        onClick={() => toggleSchedule(schedule.id, schedule.enabled)}
                        className={`p-2 rounded-md ${
                          schedule.enabled
                            ? 'text-orange-600 hover:bg-orange-50'
                            : 'text-green-600 hover:bg-green-50'
                        }`}
                        title={schedule.enabled ? 'Pausar' : 'Ativar'}
                      >
                        {schedule.enabled ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4" />}
                      </button>
                      <button
                        onClick={() => deleteSchedule(schedule.id)}
                        className="p-2 text-red-600 hover:bg-red-50 rounded-md"
                        title="Excluir"
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {activeTab === 'executions' && (
        <div className="space-y-4">
          {executions.length === 0 ? (
            <div className="text-center py-12">
              <Activity className="mx-auto h-12 w-12 text-gray-400" />
              <h3 className="mt-2 text-sm font-medium text-gray-900">Nenhuma execução</h3>
              <p className="mt-1 text-sm text-gray-500">As execuções dos agendamentos aparecerão aqui.</p>
            </div>
          ) : (
            <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Agendamento
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Tipo
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Status
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Executado em
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Duração
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {executions.map((execution) => (
                    <tr key={execution.id}>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                        {execution.schedule_name}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {getTypeLabel(execution.type)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        {getExecutionStatusBadge(execution.status)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {new Date(execution.executed_at).toLocaleString('pt-BR')}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {execution.duration ? `${execution.duration}s` : '-'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* Modal de Criação */}
      {showCreateForm && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
            <div className="mt-3">
              <h3 className="text-lg font-medium text-gray-900 mb-4">Novo Agendamento</h3>
              <form onSubmit={handleCreateSchedule} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700">Nome</label>
                  <input
                    type="text"
                    value={formData.name}
                    onChange={(e) => setFormData({...formData, name: e.target.value})}
                    className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700">Tipo</label>
                  <select
                    value={formData.type}
                    onChange={(e) => setFormData({...formData, type: e.target.value})}
                    className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2"
                  >
                    <option value="vm_shutdown">Desligar VMs</option>
                    <option value="vm_startup">Ligar VMs</option>
                    <option value="backup">Backup</option>
                    <option value="cleanup">Limpeza</option>
                    <option value="report">Relatório</option>
                    <option value="security_scan">Scan de Segurança</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700">Frequência</label>
                  <select
                    value={formData.frequency}
                    onChange={(e) => setFormData({...formData, frequency: e.target.value})}
                    className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2"
                  >
                    <option value="daily">Diário</option>
                    <option value="weekly">Semanal</option>
                    <option value="monthly">Mensal</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700">Horário</label>
                  <input
                    type="time"
                    value={formData.time}
                    onChange={(e) => setFormData({...formData, time: e.target.value})}
                    className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700">Escopo</label>
                  <select
                    value={formData.scope}
                    onChange={(e) => setFormData({...formData, scope: e.target.value})}
                    className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2"
                  >
                    <option value="subscription">Toda a Subscription</option>
                    <option value="resource_group">Resource Group Específico</option>
                    <option value="tags">Por Tags</option>
                  </select>
                </div>

                {formData.scope === 'resource_group' && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Resource Group</label>
                    <input
                      type="text"
                      value={formData.resource_group}
                      onChange={(e) => setFormData({...formData, resource_group: e.target.value})}
                      className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2"
                      placeholder="Nome do resource group"
                    />
                  </div>
                )}

                {formData.scope === 'tags' && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Tags</label>
                    <input
                      type="text"
                      value={formData.tags}
                      onChange={(e) => setFormData({...formData, tags: e.target.value})}
                      className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2"
                      placeholder="environment=prod,team=devops"
                    />
                  </div>
                )}

                <div className="flex items-center">
                  <input
                    type="checkbox"
                    checked={formData.notifications}
                    onChange={(e) => setFormData({...formData, notifications: e.target.checked})}
                    className="h-4 w-4 text-blue-600 border-gray-300 rounded"
                  />
                  <label className="ml-2 block text-sm text-gray-900">
                    Enviar notificações por email
                  </label>
                </div>

                {formData.notifications && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Email</label>
                    <input
                      type="email"
                      value={formData.email}
                      onChange={(e) => setFormData({...formData, email: e.target.value})}
                      className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2"
                      placeholder="seu@email.com"
                    />
                  </div>
                )}

                <div className="flex justify-end space-x-3 pt-4">
                  <button
                    type="button"
                    onClick={() => setShowCreateForm(false)}
                    className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-md"
                  >
                    Cancelar
                  </button>
                  <button
                    type="submit"
                    className="px-4 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-md"
                  >
                    Criar Agendamento
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default SchedulesUnifiedPage;

