"""
Implementar endpoints para criar e deletar Resource Groups
"""

@azure_test_bp.route('/create-resource-group', methods=['POST'])
def create_resource_group():
    """Cria um novo Resource Group"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Usuário não autenticado'}), 401
    
    try:
        data = request.get_json()
        name = data.get('name')
        location = data.get('location', 'East US')
        
        if not name:
            return jsonify({
                'success': False,
                'error': 'Nome do Resource Group é obrigatório'
            }), 400
        
        user_id = session['user_id']
        logger.info(f"Usuário {user_id} criando Resource Group: {name} em {location}")
        
        # Obter credenciais do usuário
        creds = AzureCredentials.get_by_user_id(user_id)
        if not creds:
            return jsonify({
                'success': False,
                'error': 'Credenciais Azure não configuradas'
            }), 400
        
        # Criar cliente Azure
        credential = ClientSecretCredential(
            creds.tenant_id,
            creds.client_id,
            creds.get_client_secret()
        )
        
        resource_client = ResourceManagementClient(credential, creds.subscription_id)
        
        # Criar Resource Group
        rg_params = {
            'location': location,
            'tags': {
                'created_by': 'BOLT_Dashboard',
                'created_at': datetime.utcnow().isoformat()
            }
        }
        
        logger.info(f"Criando Resource Group {name} com parâmetros: {rg_params}")
        
        result = resource_client.resource_groups.create_or_update(name, rg_params)
        
        logger.info(f"Resource Group {name} criado com sucesso")
        
        return jsonify({
            'success': True,
            'message': f'Resource Group "{name}" criado com sucesso',
            'resource_group': {
                'name': result.name,
                'location': result.location,
                'id': result.id,
                'tags': result.tags
            }
        }), 200
        
    except Exception as e:
        error_msg = f"Erro ao criar Resource Group: {str(e)}"
        logger.error(error_msg)
        logger.error(f"Tipo do erro: {type(e)}")
        logger.error(f"Detalhes completos: {repr(e)}")
        
        return jsonify({
            'success': False,
            'error': error_msg,
            'error_type': str(type(e)),
            'error_details': repr(e)
        }), 500

@azure_test_bp.route('/delete-resource-group', methods=['DELETE'])
def delete_resource_group():
    """Deleta um Resource Group"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Usuário não autenticado'}), 401
    
    try:
        data = request.get_json()
        name = data.get('name')
        
        if not name:
            return jsonify({
                'success': False,
                'error': 'Nome do Resource Group é obrigatório'
            }), 400
        
        user_id = session['user_id']
        logger.info(f"Usuário {user_id} deletando Resource Group: {name}")
        
        # Obter credenciais do usuário
        creds = AzureCredentials.get_by_user_id(user_id)
        if not creds:
            return jsonify({
                'success': False,
                'error': 'Credenciais Azure não configuradas'
            }), 400
        
        # Criar cliente Azure
        credential = ClientSecretCredential(
            creds.tenant_id,
            creds.client_id,
            creds.get_client_secret()
        )
        
        resource_client = ResourceManagementClient(credential, creds.subscription_id)
        
        # Verificar se o Resource Group existe
        try:
            resource_client.resource_groups.get(name)
        except Exception:
            return jsonify({
                'success': False,
                'error': f'Resource Group "{name}" não encontrado'
            }), 404
        
        # Deletar Resource Group (operação assíncrona)
        logger.info(f"Iniciando deleção do Resource Group {name}")
        
        delete_operation = resource_client.resource_groups.begin_delete(name)
        
        # Aguardar conclusão (com timeout)
        delete_operation.wait(timeout=300)  # 5 minutos
        
        logger.info(f"Resource Group {name} deletado com sucesso")
        
        return jsonify({
            'success': True,
            'message': f'Resource Group "{name}" deletado com sucesso'
        }), 200
        
    except Exception as e:
        error_msg = f"Erro ao deletar Resource Group: {str(e)}"
        logger.error(error_msg)
        logger.error(f"Tipo do erro: {type(e)}")
        logger.error(f"Detalhes completos: {repr(e)}")
        
        return jsonify({
            'success': False,
            'error': error_msg,
            'error_type': str(type(e)),
            'error_details': repr(e)
        }), 500

