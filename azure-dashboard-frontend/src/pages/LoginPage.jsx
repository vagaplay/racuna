import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext.jsx';
import { Button } from '@components/ui/button.jsx';
import { Input } from '@components/ui/input.jsx';
import { Label } from '@components/ui/label.jsx';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@components/ui/card.jsx';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5001';

const LoginPage = () => {
  const navigate = useNavigate();
  const { login, register } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isLoginMode, setIsLoginMode] = useState(true);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');

  const handleMicrosoftLogin = async () => {
    try {
      setMessage('');
      setError('');
      
      const response = await fetch(`${API_BASE_URL}/api/microsoft/login`, {
        credentials: 'include'
      });
      
      const data = await response.json();
      
      if (data.success) {
        window.location.href = data.auth_url;
      } else {
        setError(data.message || 'Erro ao iniciar login com Microsoft');
      }
    } catch (err) {
      setError('Não foi possível conectar ao servidor. Tente novamente mais tarde.');
      console.error('Erro de rede:', err);
    }
  };

  const handleLocalAuth = async (e) => {
    e.preventDefault();
    setMessage('');
    setError('');

    try {
      let result;
      
      if (isLoginMode) {
        result = await login(email, password);
        if (result.success) {
          setMessage(result.message);
          navigate('/dashboard');
        } else {
          setError(result.message);
        }
      } else {
        result = await register(email, password, email.split('@')[0]);
        if (result.success) {
          setMessage('Conta criada! Agora faça login.');
          setIsLoginMode(true);
          setEmail('');
          setPassword('');
        } else {
          setError(result.message);
        }
      }
    } catch (err) {
      setError('Não foi possível conectar ao servidor. Tente novamente mais tarde.');
      console.error('Erro de rede:', err);
    }
  };

  return (
    <div className="flex items-center justify-center min-h-screen bg-gray-100">
      <Card className="w-full max-w-md">
        <CardHeader className="space-y-1">
          <CardTitle className="text-2xl text-center">
            {isLoginMode ? 'Entrar' : 'Criar Conta'}
          </CardTitle>
          <CardDescription className="text-center">
            {isLoginMode
              ? 'Escolha como deseja acessar o dashboard' 
              : 'Crie sua conta para acessar o dashboard'}
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <Button 
            onClick={handleMicrosoftLogin}
            className="w-full bg-green-600 hover:bg-green-700"
          >
            Entrar com Microsoft Entra ID
          </Button>
          
          <div className="relative">
            <div className="absolute inset-0 flex items-center">
              <span className="w-full border-t" />
            </div>
            <div className="relative flex justify-center text-xs uppercase">
              <span className="bg-background px-2 text-muted-foreground">
                OU CONTINUE COM
              </span>
            </div>
          </div>

          <form onSubmit={handleLocalAuth} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                type="email"
                placeholder="m@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="password">Senha</Label>
              <Input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
            </div>
            
            {error && (
              <div className="text-red-600 text-sm text-center">
                {error}
              </div>
            )}
            
            {message && (
              <div className="text-green-600 text-sm text-center">
                {message}
              </div>
            )}

            <Button type="submit" className="w-full">
              {isLoginMode ? 'Entrar com Conta Local' : 'Criar Conta'}
            </Button>
          </form>

          <Button
            variant="outline"
            className="w-full"
            onClick={() => {
              setIsLoginMode(!isLoginMode);
              setMessage('');
              setError('');
              setEmail('');
              setPassword('');
            }}
          >
            {isLoginMode ? 'Não tem uma conta? Crie uma!' : 'Já tem uma conta? Entre!'}
          </Button>
        </CardContent>
      </Card>
    </div>
  );
};

export default LoginPage;

