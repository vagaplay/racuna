import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Home, User, HelpCircle, Settings, LogOut } from 'lucide-react';
import { Button } from '@components/ui/button.jsx';

const Header = () => {
  const navigate = useNavigate();

  const handleNavigation = (path) => {
    navigate(path);
  };

  const handleLogout = () => {
    // Implementar logout
    if (confirm('Tem certeza que deseja sair?')) {
      // Limpar sessão/localStorage se necessário
      navigate('/');
    }
  };

  return (
    <header className="flex items-center justify-between p-4 bg-blue-600 text-white shadow-md">
      <div className="flex items-center space-x-4">
        <h1 className="text-2xl font-bold">BOLT Dashboard</h1>
      </div>
      <nav>
        <ul className="flex space-x-4">
          <li>
            <Button 
              variant="ghost" 
              className="text-white hover:bg-blue-700"
              onClick={() => handleNavigation('/dashboard')}
            >
              <Home className="mr-2 h-5 w-5" />
              Home
            </Button>
          </li>
          <li>
            <Button 
              variant="ghost" 
              className="text-white hover:bg-blue-700"
              onClick={() => handleNavigation('/profile')}
            >
              <User className="mr-2 h-5 w-5" />
              Perfil
            </Button>
          </li>
          <li>
            <Button 
              variant="ghost" 
              className="text-white hover:bg-blue-700"
              onClick={() => handleNavigation('/help')}
            >
              <HelpCircle className="mr-2 h-5 w-5" />
              Ajuda
            </Button>
          </li>
          {/* Adicionar mais itens de menu aqui */}
        </ul>
      </nav>
      <div>
        <Button 
          variant="ghost" 
          className="text-white hover:bg-blue-700"
          onClick={handleLogout}
        >
          <LogOut className="mr-2 h-5 w-5" />
          Sair
        </Button>
      </div>
    </header>
  );
};

export default Header;


