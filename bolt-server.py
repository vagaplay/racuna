#!/usr/bin/env python3
"""
Servidor HTTP customizado para servir o BOLT Dashboard
Solução DEFINITIVA para problema de hosts bloqueados
"""

import http.server
import socketserver
import os
import json
import urllib.parse
import urllib.request
from pathlib import Path

class BoltHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    """Handler customizado que aceita qualquer host e faz proxy para API"""
    
    def __init__(self, *args, **kwargs):
        # Definir diretório dos arquivos estáticos
        self.directory = "/home/ubuntu/azure-dashboard/azure-dashboard-frontend/dist"
        super().__init__(*args, **kwargs)
    
    def end_headers(self):
        """Adicionar headers CORS permissivos com suporte a credenciais"""
        # Headers CORS específicos para o domínio atual
        origin = self.headers.get('Origin')
        if origin:
            self.send_header('Access-Control-Allow-Origin', origin)
        else:
            self.send_header('Access-Control-Allow-Origin', '*')
        
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization, Cookie')
        self.send_header('Access-Control-Allow-Credentials', 'true')
        self.send_header('Cache-Control', 'no-cache')
        super().end_headers()
    
    def do_OPTIONS(self):
        """Responder a requisições OPTIONS para CORS"""
        self.send_response(200)
        self.end_headers()
    
    def do_GET(self):
        """Servir arquivos estáticos ou fazer proxy para API"""
        if self.path.startswith('/api/'):
            self.proxy_to_backend()
        else:
            # Servir arquivos estáticos
            if self.path == '/' or not os.path.exists(os.path.join(self.directory, self.path.lstrip('/'))):
                # SPA routing - sempre servir index.html para rotas do React
                self.path = '/index.html'
            super().do_GET()
    
    def do_POST(self):
        """Fazer proxy de requisições POST para API"""
        if self.path.startswith('/api/'):
            self.proxy_to_backend()
        else:
            self.send_error(404)
    
    def do_PUT(self):
        """Fazer proxy de requisições PUT para API"""
        if self.path.startswith('/api/'):
            self.proxy_to_backend()
        else:
            self.send_error(404)
    
    def do_DELETE(self):
        """Fazer proxy de requisições DELETE para API"""
        if self.path.startswith('/api/'):
            self.proxy_to_backend()
        else:
            self.send_error(404)
    
    def proxy_to_backend(self):
        """Fazer proxy das requisições para o backend Flask"""
        try:
            # URL do backend
            backend_url = f"http://localhost:5000{self.path}"
            
            # Preparar dados da requisição
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length) if content_length > 0 else None
            
            # Criar requisição para o backend
            req = urllib.request.Request(
                backend_url,
                data=post_data,
                method=self.command
            )
            
            # Copiar headers relevantes (incluindo cookies)
            for header, value in self.headers.items():
                if header.lower() not in ['host', 'content-length']:
                    req.add_header(header, value)
            
            # Fazer requisição
            with urllib.request.urlopen(req) as response:
                # Enviar resposta
                self.send_response(response.getcode())
                
                # Copiar headers da resposta (incluindo Set-Cookie)
                for header, value in response.headers.items():
                    if header.lower() not in ['content-length', 'transfer-encoding']:
                        self.send_header(header, value)
                
                # Garantir que cookies sejam enviados corretamente
                self.send_header('Access-Control-Allow-Credentials', 'true')
                
                self.end_headers()
                
                # Copiar corpo da resposta
                self.wfile.write(response.read())
                
        except Exception as e:
            print(f"Erro no proxy: {e}")
            self.send_error(500, f"Erro no proxy: {str(e)}")
    
    def log_message(self, format, *args):
        """Log customizado"""
        print(f"[BOLT] {self.address_string()} - {format % args}")

def start_server(port=5180):
    """Iniciar servidor HTTP customizado"""
    
    # Verificar se diretório dist existe
    dist_dir = "/home/ubuntu/azure-dashboard/azure-dashboard-frontend/dist"
    if not os.path.exists(dist_dir):
        print(f"❌ Erro: Diretório {dist_dir} não encontrado!")
        print("Execute 'npm run build' primeiro.")
        return False
    
    try:
        # Mudar para diretório dist
        os.chdir(dist_dir)
        
        # Criar servidor
        with socketserver.TCPServer(("0.0.0.0", port), BoltHTTPRequestHandler) as httpd:
            print(f"🚀 BOLT Dashboard Server iniciado!")
            print(f"📊 Servindo arquivos de: {dist_dir}")
            print(f"🌐 Servidor rodando em: http://0.0.0.0:{port}")
            print(f"🔗 Acesso local: http://localhost:{port}")
            print(f"🛑 Para parar: Ctrl+C")
            print()
            
            # Iniciar servidor
            httpd.serve_forever()
            
    except KeyboardInterrupt:
        print("\n🛑 Servidor parado pelo usuário")
        return True
    except Exception as e:
        print(f"❌ Erro ao iniciar servidor: {e}")
        return False

if __name__ == "__main__":
    start_server()

