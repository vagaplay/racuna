import azure.functions as func
import logging
import json
import os
from datetime import datetime

# Importar a aplicação Flask
from src.main import app

# Criar Azure Function App
def main(req: func.HttpRequest) -> func.HttpResponse:
    """
    Azure Function que executa a aplicação Flask
    """
    logging.info('BOLT Dashboard API function processed a request.')
    
    # Configurar Flask para Azure Functions
    with app.test_request_context(
        path=req.url,
        method=req.method,
        headers=dict(req.headers),
        data=req.get_body()
    ):
        try:
            # Processar requisição através do Flask
            response = app.full_dispatch_request()
            
            # Converter resposta Flask para Azure Function Response
            return func.HttpResponse(
                body=response.get_data(),
                status_code=response.status_code,
                headers=dict(response.headers),
                mimetype=response.content_type
            )
        except Exception as e:
            logging.error(f"Erro ao processar requisição: {str(e)}")
            return func.HttpResponse(
                body=json.dumps({"error": "Internal server error"}),
                status_code=500,
                mimetype="application/json"
            )

