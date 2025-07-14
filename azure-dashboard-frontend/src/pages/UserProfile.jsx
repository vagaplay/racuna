import React, { useState } from 'react';
import { Button } from '@components/ui/button.jsx';
import { Input } from '@components/ui/input.jsx';
import { Label } from '@components/ui/label.jsx';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@components/ui/card.jsx';

const UserProfile = () => {
  const [name, setName] = useState('');
  const [phoneNumber, setPhoneNumber] = useState('');
  const [email, setEmail] = useState('');

  const handleSaveProfile = (e) => {
    e.preventDefault();
    // Lógica para salvar os dados do perfil
    console.log('Dados do perfil salvos:', { name, phoneNumber, email });
    alert('Dados do perfil atualizados com sucesso!');
  };

  return (
    <div className="flex items-center justify-center min-h-screen bg-gray-100">
      <Card className="w-full max-w-md">
        <CardHeader className="space-y-1">
          <CardTitle className="text-2xl text-center">Meu Perfil</CardTitle>
          <CardDescription className="text-center">
            Atualize suas informações de contato.
          </CardDescription>
        </CardHeader>
        <CardContent className="grid gap-4">
          <form onSubmit={handleSaveProfile} className="grid gap-4">
            <div className="grid gap-2">
              <Label htmlFor="name">Nome Completo</Label>
              <Input
                id="name"
                type="text"
                placeholder="Seu nome"
                value={name}
                onChange={(e) => setName(e.target.value)}
                required
              />
            </div>
            <div className="grid gap-2">
              <Label htmlFor="phoneNumber">Telefone</Label>
              <Input
                id="phoneNumber"
                type="tel"
                placeholder="(XX) XXXXX-XXXX"
                value={phoneNumber}
                onChange={(e) => setPhoneNumber(e.target.value)}
              />
            </div>
            <div className="grid gap-2">
              <Label htmlFor="email">Email de Contato</Label>
              <Input
                id="email"
                type="email"
                placeholder="seu.email@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </div>
            <Button type="submit" className="w-full">
              Salvar Perfil
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
};

export default UserProfile;


