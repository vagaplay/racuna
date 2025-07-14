import React, { useState, useEffect } from 'react';
import { BarChart, Bar, LineChart, Line, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';

const ReportsPage = () => {
  const [reports, setReports] = useState({
    costOptimization: null,
    resourceUtilization: null,
    securityCompliance: null,
    performanceMetrics: null
  });
  const [loading, setLoading] = useState(false);
  const [selectedReport, setSelectedReport] = useState('cost');
  const [dateRange, setDateRange] = useState('30d');
  const [exportFormat, setExportFormat] = useState('pdf');

  const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000';

  const reportTypes = [
    { id: 'cost', name: '💰 Otimização de Custos', description: 'Análise de gastos e recomendações de economia' },
    { id: 'resources', name: '🏗️ Utilização de Recursos', description: 'Eficiência e uso de recursos Azure' },
    { id: 'security', name: '🔒 Conformidade de Segurança', description: 'Verificações de segurança e compliance' },
    { id: 'performance', name: '⚡ Métricas de Performance', description: 'Desempenho e disponibilidade dos serviços' }
  ];

  const COLORS = ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6', '#06B6D4'];

  const loadReports = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${API_BASE_URL}/api/reports/generate?type=${selectedReport}&range=${dateRange}`, {
        credentials: 'include'
      });
      if (response.ok) {
        const data = await response.json();
        setReports(prev => ({ ...prev, [selectedReport]: data }));
      }
    } catch (error) {
      console.error('Erro ao carregar relatórios:', error);
    }
    setLoading(false);
  };

  const exportReport = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/reports/export`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({
          type: selectedReport,
          range: dateRange,
          format: exportFormat
        })
      });
      
      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `relatorio-${selectedReport}-${dateRange}.${exportFormat}`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
      }
    } catch (error) {
      console.error('Erro ao exportar relatório:', error);
    }
  };

  const scheduleReport = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/reports/schedule`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({
          type: selectedReport,
          frequency: 'weekly',
          email: true
        })
      });
      
      if (response.ok) {
        alert('Relatório agendado com sucesso!');
      }
    } catch (error) {
      console.error('Erro ao agendar relatório:', error);
    }
  };

  useEffect(() => {
    loadReports();
  }, [selectedReport, dateRange]);

  const renderCostOptimizationReport = () => {
    const data = reports.cost;
    if (!data) return <div>Carregando...</div>;

    return (
      <div className="space-y-6">
        {/* Resumo de Economia */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-green-50 border border-green-200 rounded-lg p-6">
            <h3 className="text-lg font-semibold text-green-800 mb-2">💰 Economia Potencial</h3>
            <p className="text-3xl font-bold text-green-600">R$ {data.potentialSavings?.toFixed(2) || '0.00'}</p>
            <p className="text-sm text-green-600 mt-1">Por mês</p>
          </div>
          
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
            <h3 className="text-lg font-semibold text-blue-800 mb-2">📊 Gasto Atual</h3>
            <p className="text-3xl font-bold text-blue-600">R$ {data.currentSpend?.toFixed(2) || '0.00'}</p>
            <p className="text-sm text-blue-600 mt-1">Este mês</p>
          </div>
          
          <div className="bg-purple-50 border border-purple-200 rounded-lg p-6">
            <h3 className="text-lg font-semibold text-purple-800 mb-2">📈 Eficiência</h3>
            <p className="text-3xl font-bold text-purple-600">{data.efficiency || '85'}%</p>
            <p className="text-sm text-purple-600 mt-1">Score de otimização</p>
          </div>
        </div>

        {/* Gráfico de Custos por Serviço */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <h3 className="text-xl font-semibold mb-4">💸 Custos por Serviço</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={data.costsByService || []}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="service" />
              <YAxis />
              <Tooltip formatter={(value) => [`R$ ${value.toFixed(2)}`, 'Custo']} />
              <Bar dataKey="cost" fill="#3B82F6" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Recomendações */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <h3 className="text-xl font-semibold mb-4">💡 Recomendações de Economia</h3>
          <div className="space-y-4">
            {(data.recommendations || []).map((rec, index) => (
              <div key={index} className="border-l-4 border-yellow-400 bg-yellow-50 p-4">
                <h4 className="font-semibold text-yellow-800">{rec.title}</h4>
                <p className="text-yellow-700 mt-1">{rec.description}</p>
                <p className="text-sm text-yellow-600 mt-2">
                  Economia estimada: <span className="font-semibold">R$ {rec.savings?.toFixed(2) || '0.00'}/mês</span>
                </p>
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  };

  const renderResourceUtilizationReport = () => {
    const data = reports.resources;
    if (!data) return <div>Carregando...</div>;

    return (
      <div className="space-y-6">
        {/* Métricas de Utilização */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <div className="bg-white rounded-lg shadow-md p-6">
            <h3 className="text-lg font-semibold mb-2">🖥️ VMs Subutilizadas</h3>
            <p className="text-3xl font-bold text-orange-600">{data.underutilizedVMs || 0}</p>
          </div>
          
          <div className="bg-white rounded-lg shadow-md p-6">
            <h3 className="text-lg font-semibold mb-2">💾 Storage Órfão</h3>
            <p className="text-3xl font-bold text-red-600">{data.orphanedStorage || 0}</p>
          </div>
          
          <div className="bg-white rounded-lg shadow-md p-6">
            <h3 className="text-lg font-semibold mb-2">🌐 IPs Não Utilizados</h3>
            <p className="text-3xl font-bold text-yellow-600">{data.unusedIPs || 0}</p>
          </div>
          
          <div className="bg-white rounded-lg shadow-md p-6">
            <h3 className="text-lg font-semibold mb-2">⚡ Eficiência Geral</h3>
            <p className="text-3xl font-bold text-green-600">{data.overallEfficiency || 78}%</p>
          </div>
        </div>

        {/* Gráfico de Pizza - Distribuição de Recursos */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <h3 className="text-xl font-semibold mb-4">📊 Distribuição de Recursos</h3>
          <ResponsiveContainer width="100%" height={400}>
            <PieChart>
              <Pie
                data={data.resourceDistribution || []}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({name, percent}) => `${name} ${(percent * 100).toFixed(0)}%`}
                outerRadius={120}
                fill="#8884d8"
                dataKey="value"
              >
                {(data.resourceDistribution || []).map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>
    );
  };

  const renderSecurityComplianceReport = () => {
    const data = reports.security;
    if (!data) return <div>Carregando...</div>;

    return (
      <div className="space-y-6">
        {/* Score de Segurança */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-white rounded-lg shadow-md p-6">
            <h3 className="text-lg font-semibold mb-2">🛡️ Score de Segurança</h3>
            <p className="text-4xl font-bold text-blue-600">{data.securityScore || 85}/100</p>
          </div>
          
          <div className="bg-white rounded-lg shadow-md p-6">
            <h3 className="text-lg font-semibold mb-2">⚠️ Vulnerabilidades</h3>
            <p className="text-4xl font-bold text-red-600">{data.vulnerabilities || 3}</p>
          </div>
          
          <div className="bg-white rounded-lg shadow-md p-6">
            <h3 className="text-lg font-semibold mb-2">✅ Compliance</h3>
            <p className="text-4xl font-bold text-green-600">{data.complianceScore || 92}%</p>
          </div>
        </div>

        {/* Verificações de Segurança */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <h3 className="text-xl font-semibold mb-4">🔍 Verificações de Segurança</h3>
          <div className="space-y-3">
            {(data.securityChecks || []).map((check, index) => (
              <div key={index} className="flex items-center justify-between p-3 border rounded-lg">
                <div className="flex items-center gap-3">
                  <span className={`text-2xl ${check.status === 'pass' ? '✅' : check.status === 'warning' ? '⚠️' : '❌'}`}>
                    {check.status === 'pass' ? '✅' : check.status === 'warning' ? '⚠️' : '❌'}
                  </span>
                  <div>
                    <h4 className="font-semibold">{check.name}</h4>
                    <p className="text-sm text-gray-600">{check.description}</p>
                  </div>
                </div>
                <span className={`px-3 py-1 rounded text-sm ${
                  check.status === 'pass' ? 'bg-green-100 text-green-800' :
                  check.status === 'warning' ? 'bg-yellow-100 text-yellow-800' :
                  'bg-red-100 text-red-800'
                }`}>
                  {check.status === 'pass' ? 'Aprovado' : check.status === 'warning' ? 'Atenção' : 'Falhou'}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  };

  const renderPerformanceReport = () => {
    const data = reports.performance;
    if (!data) return <div>Carregando...</div>;

    return (
      <div className="space-y-6">
        {/* Métricas de Performance */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <div className="bg-white rounded-lg shadow-md p-6">
            <h3 className="text-lg font-semibold mb-2">⚡ Disponibilidade</h3>
            <p className="text-3xl font-bold text-green-600">{data.availability || 99.9}%</p>
          </div>
          
          <div className="bg-white rounded-lg shadow-md p-6">
            <h3 className="text-lg font-semibold mb-2">🚀 Latência Média</h3>
            <p className="text-3xl font-bold text-blue-600">{data.avgLatency || 45}ms</p>
          </div>
          
          <div className="bg-white rounded-lg shadow-md p-6">
            <h3 className="text-lg font-semibold mb-2">📈 Throughput</h3>
            <p className="text-3xl font-bold text-purple-600">{data.throughput || 1250}/s</p>
          </div>
          
          <div className="bg-white rounded-lg shadow-md p-6">
            <h3 className="text-lg font-semibold mb-2">❌ Taxa de Erro</h3>
            <p className="text-3xl font-bold text-red-600">{data.errorRate || 0.1}%</p>
          </div>
        </div>

        {/* Gráfico de Performance ao Longo do Tempo */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <h3 className="text-xl font-semibold mb-4">📊 Performance ao Longo do Tempo</h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={data.performanceHistory || []}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="timestamp" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Line type="monotone" dataKey="latency" stroke="#3B82F6" name="Latência (ms)" />
              <Line type="monotone" dataKey="throughput" stroke="#10B981" name="Throughput" />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>
    );
  };

  const renderReportContent = () => {
    switch (selectedReport) {
      case 'cost':
        return renderCostOptimizationReport();
      case 'resources':
        return renderResourceUtilizationReport();
      case 'security':
        return renderSecurityComplianceReport();
      case 'performance':
        return renderPerformanceReport();
      default:
        return <div>Selecione um tipo de relatório</div>;
    }
  };

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold">📊 Relatórios e Analytics</h1>
        <div className="flex gap-3">
          <select
            value={dateRange}
            onChange={(e) => setDateRange(e.target.value)}
            className="border rounded-lg px-3 py-2"
          >
            <option value="7d">Últimos 7 dias</option>
            <option value="30d">Últimos 30 dias</option>
            <option value="90d">Últimos 90 dias</option>
            <option value="1y">Último ano</option>
          </select>
          
          <select
            value={exportFormat}
            onChange={(e) => setExportFormat(e.target.value)}
            className="border rounded-lg px-3 py-2"
          >
            <option value="pdf">PDF</option>
            <option value="excel">Excel</option>
            <option value="csv">CSV</option>
          </select>
          
          <button
            onClick={exportReport}
            className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700"
          >
            📥 Exportar
          </button>
          
          <button
            onClick={scheduleReport}
            className="bg-purple-600 text-white px-4 py-2 rounded-lg hover:bg-purple-700"
          >
            📅 Agendar
          </button>
        </div>
      </div>

      {/* Seletor de Tipo de Relatório */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        {reportTypes.map(type => (
          <button
            key={type.id}
            onClick={() => setSelectedReport(type.id)}
            className={`p-4 rounded-lg border-2 text-left transition-all ${
              selectedReport === type.id
                ? 'border-blue-500 bg-blue-50'
                : 'border-gray-200 hover:border-gray-300'
            }`}
          >
            <h3 className="font-semibold mb-1">{type.name}</h3>
            <p className="text-sm text-gray-600">{type.description}</p>
          </button>
        ))}
      </div>

      {/* Conteúdo do Relatório */}
      <div className="min-h-96">
        {loading ? (
          <div className="flex items-center justify-center h-64">
            <div className="text-xl">🔄 Gerando relatório...</div>
          </div>
        ) : (
          renderReportContent()
        )}
      </div>
    </div>
  );
};

export default ReportsPage;

