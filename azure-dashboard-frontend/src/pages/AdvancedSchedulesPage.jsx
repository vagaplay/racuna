import React, { useState, useEffect } from 'react';

const AdvancedSchedulesPage = () => {
  const [schedules, setSchedules] = useState([]);
  const [loading, setLoading] = useState(false);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [newSchedule, setNewSchedule] = useState({
    name: '',
    type: 'vm_shutdown',
    schedule_type: 'daily',
    time: '19:00',
    days_of_week: [],
    target_scope: 'resource_group',
    target_value: '',
    enabled: true,
    notification_email: '',
    description: ''
  });

  const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000';

  const scheduleTypes = [
    { value: 'vm_shutdown', label: '🔌 Shutdown de VMs', description: 'Desligar VMs automaticamente' },
    { value: 'vm_startup', label: '▶️ Startup de VMs', description: 'Ligar VMs automaticamente' },
    { value: 'backup_resources', label: '💾 Backup de Recursos', description: 'Backup automático de recursos críticos' },
    { value: 'cleanup_resources', label: '🧹 Limpeza de Recursos', description: 'Remover recursos não utilizados' },
    { value: 'cost_report', label: '📊 Relatório de Custos', description: 'Enviar relatório de custos por email' },
    { value: 'security_scan', label: '🔒 Scan de Segurança', description: 'Verificar configurações de segurança' }
  ];

  const daysOfWeek = [
    { value: 'monday', label: 'Segunda' },
    { value: 'tuesday', label: 'Terça' },
    { value: 'wednesday', label: 'Quarta' },
    { value: 'thursday', label: 'Quinta' },
    { value: 'friday', label: 'Sexta' },
    { value: 'saturday', label: 'Sábado' },
    { value: 'sunday', label: 'Domingo' }
  ];

  const loadSchedules = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${API_BASE_URL}/api/schedules`, {
        credentials: 'include'
      });
      if (response.ok) {
        const data = await response.json();
        setSchedules(data.schedules || []);
      }
    } catch (error) {
      console.error('Erro ao carregar agendamentos:', error);
    }
    setLoading(false);
  };

  const createSchedule = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${API_BASE_URL}/api/schedules`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify(newSchedule)
      });
      
      if (response.ok) {
        await loadSchedules();
        setShowCreateForm(false);
        setNewSchedule({
          name: '',
          type: 'vm_shutdown',
          schedule_type: 'daily',
          time: '19:00',
          days_of_week: [],
          target_scope: 'resource_group',
          target_value: '',
          enabled: true,
          notification_email: '',
          description: ''
        });
      }
    } catch (error) {
      console.error('Erro ao criar agendamento:', error);
    }
    setLoading(false);
  };

  const toggleSchedule = async (scheduleId, enabled) => {
    try {
      await fetch(`${API_BASE_URL}/api/schedules/${scheduleId}/toggle`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ enabled })
      });
      await loadSchedules();
    } catch (error) {
      console.error('Erro ao alterar status do agendamento:', error);
    }
  };

  const deleteSchedule = async (scheduleId) => {
    if (confirm('Tem certeza que deseja excluir este agendamento?')) {
      try {
        await fetch(`${API_BASE_URL}/api/schedules/${scheduleId}`, {
          method: 'DELETE',
          credentials: 'include'
        });
        await loadSchedules();
      } catch (error) {
        console.error('Erro ao excluir agendamento:', error);
      }
    }
  };

  useEffect(() => {
    loadSchedules();
  }, []);

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold">📅 Agendamentos Avançados</h1>
        <button
          onClick={() => setShowCreateForm(true)}
          className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700"
        >
          ➕ Novo Agendamento
        </button>
      </div>

      {/* Lista de Agendamentos */}
      <div className="grid gap-4 mb-6">
        {schedules.map(schedule => (
          <div key={schedule.id} className="bg-white rounded-lg shadow-md p-6">
            <div className="flex justify-between items-start">
              <div className="flex-1">
                <div className="flex items-center gap-3 mb-2">
                  <h3 className="text-xl font-semibold">{schedule.name}</h3>
                  <span className={`px-2 py-1 rounded text-sm ${
                    schedule.enabled ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
                  }`}>
                    {schedule.enabled ? '✅ Ativo' : '⏸️ Pausado'}
                  </span>
                </div>
                
                <p className="text-gray-600 mb-3">{schedule.description}</p>
                
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                  <div>
                    <span className="font-medium">Tipo:</span>
                    <p>{scheduleTypes.find(t => t.value === schedule.type)?.label}</p>
                  </div>
                  <div>
                    <span className="font-medium">Horário:</span>
                    <p>{schedule.time}</p>
                  </div>
                  <div>
                    <span className="font-medium">Frequência:</span>
                    <p>{schedule.schedule_type === 'daily' ? 'Diário' : 'Semanal'}</p>
                  </div>
                  <div>
                    <span className="font-medium">Escopo:</span>
                    <p>{schedule.target_scope}: {schedule.target_value}</p>
                  </div>
                </div>
              </div>
              
              <div className="flex gap-2 ml-4">
                <button
                  onClick={() => toggleSchedule(schedule.id, !schedule.enabled)}
                  className={`px-3 py-1 rounded text-sm ${
                    schedule.enabled 
                      ? 'bg-yellow-100 text-yellow-800 hover:bg-yellow-200' 
                      : 'bg-green-100 text-green-800 hover:bg-green-200'
                  }`}
                >
                  {schedule.enabled ? '⏸️ Pausar' : '▶️ Ativar'}
                </button>
                <button
                  onClick={() => deleteSchedule(schedule.id)}
                  className="px-3 py-1 bg-red-100 text-red-800 rounded text-sm hover:bg-red-200"
                >
                  🗑️ Excluir
                </button>
              </div>
            </div>
          </div>
        ))}
        
        {schedules.length === 0 && !loading && (
          <div className="text-center py-12 text-gray-500">
            <p className="text-xl mb-2">📅 Nenhum agendamento configurado</p>
            <p>Clique em "Novo Agendamento" para começar</p>
          </div>
        )}
      </div>

      {/* Modal de Criação */}
      {showCreateForm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-2xl max-h-[90vh] overflow-y-auto">
            <h2 className="text-2xl font-bold mb-4">➕ Novo Agendamento</h2>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-1">Nome do Agendamento</label>
                <input
                  type="text"
                  value={newSchedule.name}
                  onChange={(e) => setNewSchedule({...newSchedule, name: e.target.value})}
                  className="w-full border rounded-lg px-3 py-2"
                  placeholder="Ex: Shutdown VMs Desenvolvimento"
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-1">Tipo de Ação</label>
                <select
                  value={newSchedule.type}
                  onChange={(e) => setNewSchedule({...newSchedule, type: e.target.value})}
                  className="w-full border rounded-lg px-3 py-2"
                >
                  {scheduleTypes.map(type => (
                    <option key={type.value} value={type.value}>
                      {type.label} - {type.description}
                    </option>
                  ))}
                </select>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-1">Frequência</label>
                  <select
                    value={newSchedule.schedule_type}
                    onChange={(e) => setNewSchedule({...newSchedule, schedule_type: e.target.value})}
                    className="w-full border rounded-lg px-3 py-2"
                  >
                    <option value="daily">Diário</option>
                    <option value="weekly">Semanal</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium mb-1">Horário</label>
                  <input
                    type="time"
                    value={newSchedule.time}
                    onChange={(e) => setNewSchedule({...newSchedule, time: e.target.value})}
                    className="w-full border rounded-lg px-3 py-2"
                  />
                </div>
              </div>

              {newSchedule.schedule_type === 'weekly' && (
                <div>
                  <label className="block text-sm font-medium mb-1">Dias da Semana</label>
                  <div className="grid grid-cols-4 gap-2">
                    {daysOfWeek.map(day => (
                      <label key={day.value} className="flex items-center">
                        <input
                          type="checkbox"
                          checked={newSchedule.days_of_week.includes(day.value)}
                          onChange={(e) => {
                            const days = e.target.checked
                              ? [...newSchedule.days_of_week, day.value]
                              : newSchedule.days_of_week.filter(d => d !== day.value);
                            setNewSchedule({...newSchedule, days_of_week: days});
                          }}
                          className="mr-2"
                        />
                        {day.label}
                      </label>
                    ))}
                  </div>
                </div>
              )}

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-1">Escopo</label>
                  <select
                    value={newSchedule.target_scope}
                    onChange={(e) => setNewSchedule({...newSchedule, target_scope: e.target.value})}
                    className="w-full border rounded-lg px-3 py-2"
                  >
                    <option value="subscription">Subscription Inteira</option>
                    <option value="resource_group">Resource Group</option>
                    <option value="tag">Por Tag</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium mb-1">
                    {newSchedule.target_scope === 'resource_group' ? 'Nome do Resource Group' :
                     newSchedule.target_scope === 'tag' ? 'Tag (chave=valor)' : 'ID da Subscription'}
                  </label>
                  <input
                    type="text"
                    value={newSchedule.target_value}
                    onChange={(e) => setNewSchedule({...newSchedule, target_value: e.target.value})}
                    className="w-full border rounded-lg px-3 py-2"
                    placeholder={
                      newSchedule.target_scope === 'resource_group' ? 'rg-desenvolvimento' :
                      newSchedule.target_scope === 'tag' ? 'Environment=Development' : 'subscription-id'
                    }
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium mb-1">Email para Notificações (opcional)</label>
                <input
                  type="email"
                  value={newSchedule.notification_email}
                  onChange={(e) => setNewSchedule({...newSchedule, notification_email: e.target.value})}
                  className="w-full border rounded-lg px-3 py-2"
                  placeholder="seu@email.com"
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-1">Descrição</label>
                <textarea
                  value={newSchedule.description}
                  onChange={(e) => setNewSchedule({...newSchedule, description: e.target.value})}
                  className="w-full border rounded-lg px-3 py-2"
                  rows="3"
                  placeholder="Descreva o propósito deste agendamento..."
                />
              </div>
            </div>

            <div className="flex justify-end gap-3 mt-6">
              <button
                onClick={() => setShowCreateForm(false)}
                className="px-4 py-2 text-gray-600 border rounded-lg hover:bg-gray-50"
              >
                Cancelar
              </button>
              <button
                onClick={createSchedule}
                disabled={loading || !newSchedule.name || !newSchedule.target_value}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
              >
                {loading ? 'Criando...' : 'Criar Agendamento'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AdvancedSchedulesPage;

