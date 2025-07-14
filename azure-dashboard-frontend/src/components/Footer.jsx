import React from 'react';

const Footer = () => {
  return (
    <footer className="p-4 bg-gray-200 text-center text-gray-600 text-sm">
      © {new Date().getFullYear()} Azure Dashboard. Todos os direitos reservados.
    </footer>
  );
};

export default Footer;


