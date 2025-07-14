import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@components/ui/card.jsx';

const HelpPage = () => {
  const [supportEmail, setSupportEmail] = useState('suporte@suaempresa.com'); // Valor padrão, será carregado do backend

  useEffect(() => {
    // Em uma implementação real, você faria uma chamada API aqui para buscar o email de suporte
    // Ex: fetch('/api/settings/support-email').then(res => res.json()).then(data => setSupportEmail(data.email));
  }, []);

  return (
    <div className="flex items-center justify-center min-h-screen bg-gray-100">
      <Card className="w-full max-w-md">
        <CardHeader className="space-y-1">
          <CardTitle className="text-2xl text-center">Ajuda e Suporte</CardTitle>
          <CardDescription className="text-center">
            Encontre informações de contato para suporte.
          </CardDescription>
        </CardHeader>
        <CardContent className="grid gap-4 text-center">
          <p className="text-lg">
            Para qualquer dúvida ou problema, entre em contato com nossa equipe de suporte:
          </p>
          <p className="text-2xl font-bold text-blue-600">
            <a href={`mailto:${supportEmail}`}>{supportEmail}</a>
          </p>
          <p className="text-sm text-gray-500">
            Nossa equipe está disponível para ajudá-lo.
          </p>
        </CardContent>
      </Card>
    </div>
  );
};

export default HelpPage;


