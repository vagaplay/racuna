import os
import re

def get_dynamic_cors_origins():
    """
    Gera lista dinâmica de origens CORS baseada no ambiente atual.
    Resolve automaticamente o problema de hosts bloqueados.
    """
    origins = [
        "http://localhost:5174",
        "http://localhost:5175", 
        "http://localhost:5176",
        "http://127.0.0.1:5174",
        "http://127.0.0.1:5175",
        "http://127.0.0.1:5176"
    ]
    
    # Detectar hostname atual do sandbox
    try:
        hostname = os.popen('hostname').read().strip()
        if hostname and 'sandbox' in hostname:
            # Extrair ID único do hostname
            hostname_parts = hostname.split('-')
            if len(hostname_parts) >= 2:
                unique_id = '-'.join(hostname_parts[1:])
                
                # Adicionar todas as possíveis portas para este ID
                for port in [5174, 5175, 5176]:
                    origins.append(f"https://{port}-{unique_id}.manusvm.computer")
    except:
        pass
    
    # Adicionar padrões conhecidos (fallback)
    known_patterns = [
        "ia3ykdj47iiiq3zz55oz3",
        "ihsyzxcnscfqw4bg8mtla", 
        "inabjzwbj0x048r6cvapm"
    ]
    
    for pattern in known_patterns:
        for port in [5174, 5175, 5176, 5177, 5180, 5181, 5182]:
            origins.append(f"https://{port}-{pattern}-f94a1eb6.manusvm.computer")
            origins.append(f"https://{port}-{pattern}-cfd6f59a.manusvm.computer")
    
    # Remover duplicatas e retornar
    return list(set(origins))

def get_cors_config():
    """
    Retorna configuração completa do CORS.
    """
    return {
        'resources': {r"/api/*": {"origins": get_dynamic_cors_origins()}},
        'supports_credentials': True,
        'allow_headers': ['Content-Type', 'Authorization'],
        'methods': ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS']
    }

