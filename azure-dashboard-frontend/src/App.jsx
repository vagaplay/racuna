import React from 'react';
import { Outlet, useLocation } from 'react-router-dom';
import Header from './components/Header.jsx';
import Sidebar from './components/Sidebar.jsx';
import Footer from './components/Footer.jsx';
import './App.css';

function App() {
  const location = useLocation();
  const isLoginPage = location.pathname === '/';

  return (
    <div className="flex flex-col min-h-screen">
      {!isLoginPage && <Header />}
      <div className="flex flex-1">
        {!isLoginPage && <Sidebar />}
        <main className="flex-1 p-4 bg-gray-100">
          <Outlet /> {/* Renderiza o conteúdo da rota aninhada aqui */}
        </main>
      </div>
      {!isLoginPage && <Footer />}
    </div>
  );
}

export default App;


