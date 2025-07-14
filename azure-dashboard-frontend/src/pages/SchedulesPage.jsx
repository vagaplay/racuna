import React, { useState, useEffect } from 'react';
import { Calendar, Clock, Play, Pause, Settings, Plus, CheckCircle, AlertCircle } from 'lucide-react';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

const SchedulesPage = () => {
  const [schedules, setSchedules] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    loadSchedules();
  }, []);

  const loadSchedules = async () => {
    try {
      setLoading(true);
      // Simular dados de agendamentos
      setTimeout(() => {
        setSchedules([
          {
            id: 1,
            name: 'Verificação de Lock Mensal',
            description: 'Verifica se o lock de prevenção de gastos está ativo',
            schedule: 'Todo dia 02 às 08:00',
            status: 'active',
            lastRun: '2024-01-02T08:00:00Z',
            nextRun: '2024-02-02T08:00:00Z',
            type: 'lock-check'
          },
          {
            id: 2,
            name: 'Shutdown de Recursos',
            description: 'Desliga recursos não essenciais fora do horário comercial',
            schedule: 'Segunda a Sexta às 19:00',
            status: 'active',
            lastRun: '2024-01-15T19:00:00Z',
            nextRun: '2024-01-16T19:00:00Z',
            type: 'shutdown'
          },
          {
            id: 3,
            name: 'Limpeza de Recursos sem Tags',
            description: 'Remove recursos que não possuem tags obrigatórias',
            schedule: 'Segunda a Sexta às 19:00',
            status: 'active',
            lastRun: '2024-01-15T19:00:00Z',
            nextRun: '2024-01-16T19:00:00Z',
            type: 'cleanup'
          },
          {
            id: 4,
            name: 'Remoção de Locks por Budget',
            description: 'Remove locks quando o orçamento é excedido',
            schedule: 'Sob demanda (trigger por budget)',
            status: 'standby',
            lastRun: 'Nunca',
            nextRun: 'Aguardando trigger',
            type: 'budget-unlock'
          }
        ]);
        setLoading(false);
      }, 1000);
    } catch (error) {
      setError('Erro ao carregar agendamentos');
      setLoading(false);
    }
  };

  const toggleSchedule = (id) => {
    setSchedules(schedules.map(schedule => 
      schedule.id === id 
        ? { ...schedule, status: schedule.status === 'active' ? 'paused' : 'active' }
        : schedule
    ));
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'active':
        return <CheckCircle className="h-5 w-5 text-green-500" />;
      case 'paused':
        return <Pause className="h-5 w-5 text-yellow-500" />;
      case 'standby':
        return <Clock className="h-5 w-5 text-blue-500" />;
      default:
        return <AlertCircle className="h-5 w-5 text-red-500" />;
    }
  };

  const getStatusText = (status) => {
    switch (status) {
      case 'active':
        return 'Ativo';
      case 'paused':
        return 'Pausado';
      case 'standby':
        return 'Standby';
      default:
        return 'Erro';
    }
  };

  const formatDate = (dateString) => {
    if (dateString === 'Nunca' || dateString === 'Aguardando trigger') {
      return dateString;
    }
    return new Date(dateString).toLocaleString('pt-BR');
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-lg">Carregando agendamentos...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <div className="flex items-center">
          <AlertCircle className="h-5 w-5 text-red-500 mr-2" />
          <span className="text-red-700">{error}</span>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold text-gray-900">Agendamentos</h1>
        <div className="flex space-x-3">
          <button 
            onClick={loadSchedules}
            className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            <Calendar className="h-4 w-4 mr-2" />
            Atualizar
          </button>
          <button className="flex items-center px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700">
            <Plus className="h-4 w-4 mr-2" />
            Novo Agendamento
          </button>
        </div>
      </div>

      {/* Resumo */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <CheckCircle className="h-8 w-8 text-green-600" />
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Ativos</p>
              <p className="text-2xl font-bold text-gray-900">
                {schedules.filter(s => s.status === 'active').length}
              </p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <Pause className="h-8 w-8 text-yellow-600" />
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Pausados</p>
              <p className="text-2xl font-bold text-gray-900">
                {schedules.filter(s => s.status === 'paused').length}
              </p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <Clock className="h-8 w-8 text-blue-600" />
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Standby</p>
              <p className="text-2xl font-bold text-gray-900">
                {schedules.filter(s => s.status === 'standby').length}
              </p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <Calendar className="h-8 w-8 text-purple-600" />
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Total</p>
              <p className="text-2xl font-bold text-gray-900">
                {schedules.length}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Lista de Agendamentos */}
      <div className="bg-white rounded-lg shadow">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-xl font-semibold">Agendamentos Configurados</h2>
        </div>
        <div className="divide-y divide-gray-200">
          {schedules.map((schedule) => (
            <div key={schedule.id} className="p-6">
              <div className="flex items-center justify-between">
                <div className="flex-1">
                  <div className="flex items-center space-x-3">
                    {getStatusIcon(schedule.status)}
                    <h3 className="text-lg font-medium text-gray-900">{schedule.name}</h3>
                    <span className={`px-2 py-1 text-xs rounded-full ${
                      schedule.status === 'active' 
                        ? 'bg-green-100 text-green-800'
                        : schedule.status === 'paused'
                        ? 'bg-yellow-100 text-yellow-800'
                        : 'bg-blue-100 text-blue-800'
                    }`}>
                      {getStatusText(schedule.status)}
                    </span>
                  </div>
                  <p className="text-gray-600 mt-1">{schedule.description}</p>
                  <div className="mt-3 grid grid-cols-1 md:grid-cols-3 gap-4 text-sm text-gray-500">
                    <div>
                      <span className="font-medium">Agendamento:</span> {schedule.schedule}
                    </div>
                    <div>
                      <span className="font-medium">Última execução:</span> {formatDate(schedule.lastRun)}
                    </div>
                    <div>
                      <span className="font-medium">Próxima execução:</span> {formatDate(schedule.nextRun)}
                    </div>
                  </div>
                </div>
                <div className="flex items-center space-x-2 ml-4">
                  <button
                    onClick={() => toggleSchedule(schedule.id)}
                    className={`px-3 py-1 rounded text-sm font-medium ${
                      schedule.status === 'active'
                        ? 'bg-yellow-100 text-yellow-800 hover:bg-yellow-200'
                        : 'bg-green-100 text-green-800 hover:bg-green-200'
                    }`}
                  >
                    {schedule.status === 'active' ? 'Pausar' : 'Ativar'}
                  </button>
                  <button className="p-2 text-gray-400 hover:text-gray-600">
                    <Settings className="h-4 w-4" />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Próximas Execuções */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold mb-4">Próximas Execuções</h2>
        <div className="space-y-3">
          {schedules
            .filter(s => s.status === 'active' && s.nextRun !== 'Aguardando trigger')
            .sort((a, b) => new Date(a.nextRun) - new Date(b.nextRun))
            .slice(0, 5)
            .map((schedule) => (
              <div key={schedule.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div>
                  <span className="font-medium">{schedule.name}</span>
                  <span className="text-gray-500 ml-2">({schedule.schedule})</span>
                </div>
                <span className="text-sm text-gray-600">{formatDate(schedule.nextRun)}</span>
              </div>
            ))}
        </div>
      </div>
    </div>
  );
};

export default SchedulesPage;

