#!/usr/bin/env python3
"""
Servidor proxy simples para BOLT Dashboard
Serve arquivos estáticos e faz proxy das APIs para o backend
"""

import http.server
import socketserver
import urllib.request
import urllib.parse
import json
import os
from urllib.error import URLError

class ProxyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory="/home/ubuntu/azure-dashboard/azure-dashboard-frontend/dist", **kwargs)
    
    def do_GET(self):
        if self.path.startswith('/api/'):
            self.proxy_request()
        else:
            # Servir arquivos estáticos
            if self.path == '/':
                self.path = '/index.html'
            elif not os.path.exists(os.path.join(self.directory, self.path.lstrip('/'))):
                # Para SPA, redirecionar para index.html
                self.path = '/index.html'
            super().do_GET()
    
    def do_POST(self):
        if self.path.startswith('/api/'):
            self.proxy_request()
        else:
            self.send_error(404)
    
    def do_PUT(self):
        if self.path.startswith('/api/'):
            self.proxy_request()
        else:
            self.send_error(404)
    
    def do_DELETE(self):
        if self.path.startswith('/api/'):
            self.proxy_request()
        else:
            self.send_error(404)
    
    def proxy_request(self):
        """Fazer proxy da requisição para o backend Flask"""
        try:
            # URL do backend
            backend_url = f"http://localhost:5000{self.path}"
            
            # Preparar dados da requisição
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length) if content_length > 0 else None
            
            # Preparar headers - incluir cookies
            headers = {}
            for header_name, header_value in self.headers.items():
                if header_name.lower() not in ['host']:
                    headers[header_name] = header_value
            
            # Criar requisição
            req = urllib.request.Request(
                backend_url,
                data=post_data,
                headers=headers,
                method=self.command
            )
            
            # Fazer requisição
            with urllib.request.urlopen(req, timeout=30) as response:
                # Enviar status
                self.send_response(response.status)
                
                # Enviar headers (incluindo Set-Cookie)
                for header_name, header_value in response.headers.items():
                    if header_name.lower() not in ['transfer-encoding']:
                        self.send_header(header_name, header_value)
                
                # Headers CORS
                self.send_header('Access-Control-Allow-Origin', self.headers.get('Origin', '*'))
                self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
                self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization, Cookie')
                self.send_header('Access-Control-Allow-Credentials', 'true')
                
                # Ler resposta
                response_data = response.read()
                if 'Content-Length' not in [h for h, v in response.headers.items()]:
                    self.send_header('Content-Length', str(len(response_data)))
                self.end_headers()
                
                # Enviar dados
                self.wfile.write(response_data)
                
        except URLError as e:
            print(f"Erro de proxy: {e}")
            self.send_response(502)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            error_response = json.dumps({"error": f"Backend não disponível: {e}"}).encode()
            self.wfile.write(error_response)
        except Exception as e:
            print(f"Erro interno: {e}")
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            error_response = json.dumps({"error": f"Erro interno: {e}"}).encode()
            self.wfile.write(error_response)
    
    def do_OPTIONS(self):
        """Lidar com requisições OPTIONS para CORS"""
        if self.path.startswith('/api/'):
            self.send_response(200)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
            self.send_header('Access-Control-Allow-Credentials', 'true')
            self.end_headers()
        else:
            super().do_OPTIONS()

if __name__ == "__main__":
    PORT = 8081
    
    with socketserver.TCPServer(("0.0.0.0", PORT), ProxyHTTPRequestHandler) as httpd:
        print(f"🚀 BOLT Dashboard Proxy rodando na porta {PORT}")
        print(f"📊 Frontend: Servindo arquivos de /home/ubuntu/azure-dashboard/azure-dashboard-frontend/dist")
        print(f"🔗 Backend: Proxy para http://localhost:5000")
        print(f"🌐 Acesse: http://localhost:{PORT}")
        httpd.serve_forever()

