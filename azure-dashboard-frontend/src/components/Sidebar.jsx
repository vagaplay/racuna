import React from 'react';
import { Link } from 'react-router-dom';
import { Home, DollarSign, Settings, HelpCircle, User, CalendarDays, Zap, Cloud } from 'lucide-react';

const Sidebar = () => {
  return (
    <aside className="w-64 bg-gray-800 text-white p-4 space-y-4">
      <div className="text-2xl font-bold mb-6">Dashboard</div>
      <nav className="space-y-2">
        <Link to="/dashboard" className="flex items-center space-x-2 p-2 rounded-md hover:bg-gray-700">
          <Home className="h-5 w-5" />
          <span>Home</span>
        </Link>
        <Link to="/budget" className="flex items-center space-x-2 p-2 rounded-md hover:bg-gray-700">
          <DollarSign className="h-5 w-5" />
          <span>Orçamento</span>
        </Link>
        <Link to="/schedules-unified" className="flex items-center space-x-2 p-2 rounded-md hover:bg-gray-700">
          <CalendarDays className="h-5 w-5" />
          <span>📅 Agendamentos</span>
        </Link>
        <Link to="/actions" className="flex items-center space-x-2 p-2 rounded-md hover:bg-gray-700">
          <Zap className="h-5 w-5" />
          <span>Ações</span>
        </Link>
        <Link to="/monitoring" className="flex items-center space-x-2 p-2 rounded-md hover:bg-gray-700">
          <Zap className="h-5 w-5" />
          <span>📊 Monitoramento</span>
        </Link>
        <Link to="/reports" className="flex items-center space-x-2 p-2 rounded-md hover:bg-gray-700">
          <Zap className="h-5 w-5" />
          <span>📋 Relatórios</span>
        </Link>
        <Link to="/profile" className="flex items-center space-x-2 p-2 rounded-md hover:bg-gray-700">
          <User className="h-5 w-5" />
          <span>Perfil</span>
        </Link>
          <Link to="/azure-config" className="flex items-center space-x-2 p-2 rounded-md hover:bg-gray-700">
          <Cloud className="h-5 w-5" />
          <span>Config. Azure</span>
        </Link>
        
        <Link to="/microsoft-config" className="flex items-center space-x-2 p-2 rounded-md hover:bg-gray-700">
          <Settings className="h-5 w-5" />
          <span>Config. Microsoft</span>
        </Link>
        <Link to="/azure-functions-config" className="flex items-center space-x-2 p-2 rounded-md hover:bg-gray-700">
          <Zap className="h-5 w-5" />
          <span>Config. Functions</span>
        </Link>
        <Link to="/help" className="flex items-center space-x-2 p-2 rounded-md hover:bg-gray-700">
          <HelpCircle className="h-5 w-5" />
          <span>Ajuda</span>
        </Link>
      </nav>
    </aside>
  );
};

export default Sidebar;


