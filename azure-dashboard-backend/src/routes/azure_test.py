"""
Endpoint para criar Resource Group de teste
"""

from flask import Blueprint, request, jsonify, session
from src.services.azure_service import azure_auth_service
from azure.identity import ClientSecretCredential
from azure.mgmt.resource import ResourceManagementClient
import logging

logger = logging.getLogger(__name__)

azure_test_bp = Blueprint('azure_test', __name__)

@azure_test_bp.route('/create-resource-group', methods=['POST'])
def create_test_resource_group():
    """Cria um Resource Group de teste"""
    try:
        if 'user_id' not in session:
            return jsonify({'error': 'Usuário não autenticado'}), 401
        
        user_id = session['user_id']
        data = request.get_json() or {}
        
        # Nome do Resource Group
        rg_name = data.get('name', 'bolt-dashboard-test-rg')
        location = data.get('location', 'East US')
        
        logger.info(f"Tentando criar Resource Group '{rg_name}' para usuário {user_id}")
        
        # Obter credenciais
        if not azure_auth_service.is_user_authenticated(user_id):
            return jsonify({'error': 'Credenciais Azure não configuradas'}), 400
        
        creds = azure_auth_service.get_user_credentials(user_id)
        
        # Criar cliente
        credential = ClientSecretCredential(
            tenant_id=creds.tenant_id,
            client_id=creds.client_id,
            client_secret=creds.get_client_secret()
        )
        
        resource_client = ResourceManagementClient(credential, creds.subscription_id)
        
        logger.info(f"Cliente criado com sucesso. Subscription: {creds.subscription_id}")
        
        # Parâmetros do Resource Group
        rg_params = {
            'location': location,
            'tags': {
                'created_by': 'BOLT Dashboard',
                'purpose': 'test',
                'environment': 'development'
            }
        }
        
        logger.info(f"Criando Resource Group com parâmetros: {rg_params}")
        
        # Criar Resource Group
        result = resource_client.resource_groups.create_or_update(
            resource_group_name=rg_name,
            parameters=rg_params
        )
        
        logger.info(f"Resource Group '{rg_name}' criado com sucesso!")
        
        return jsonify({
            'success': True,
            'message': f'Resource Group "{rg_name}" criado com sucesso',
            'resource_group': {
                'name': result.name,
                'location': result.location,
                'id': result.id,
                'tags': result.tags or {},
                'properties': result.properties.__dict__ if hasattr(result, 'properties') and result.properties else {}
            }
        }), 200
        
    except Exception as e:
        error_msg = f"Erro ao criar Resource Group: {str(e)}"
        logger.error(error_msg)
        return jsonify({
            'success': False,
            'error': error_msg,
            'details': str(e)
        }), 500

@azure_test_bp.route('/list-resource-groups', methods=['GET'])
def list_resource_groups():
    """Lista Resource Groups existentes"""
    try:
        if 'user_id' not in session:
            return jsonify({'error': 'Usuário não autenticado'}), 401
        
        user_id = session['user_id']
        
        logger.info(f"Listando Resource Groups para usuário {user_id}")
        
        # Obter credenciais
        if not azure_auth_service.is_user_authenticated(user_id):
            return jsonify({'error': 'Credenciais Azure não configuradas'}), 400
        
        creds = azure_auth_service.get_user_credentials(user_id)
        
        # Criar cliente
        credential = ClientSecretCredential(
            tenant_id=creds.tenant_id,
            client_id=creds.client_id,
            client_secret=creds.get_client_secret()
        )
        
        resource_client = ResourceManagementClient(credential, creds.subscription_id)
        
        logger.info(f"Cliente criado. Listando Resource Groups...")
        
        # Listar Resource Groups
        resource_groups = list(resource_client.resource_groups.list())
        
        rg_data = []
        for rg in resource_groups:
            rg_data.append({
                'name': rg.name,
                'location': rg.location,
                'id': rg.id,
                'tags': rg.tags or {},
                'properties': rg.properties.__dict__ if hasattr(rg, 'properties') and rg.properties else {}
            })
        
        logger.info(f"Encontrados {len(rg_data)} Resource Groups")
        
        return jsonify({
            'success': True,
            'resource_groups': rg_data,
            'count': len(rg_data)
        }), 200
        
    except Exception as e:
        error_msg = f"Erro ao listar Resource Groups: {str(e)}"
        logger.error(error_msg)
        logger.error(f"Tipo do erro: {type(e)}")
        logger.error(f"Detalhes completos: {repr(e)}")
        
        return jsonify({
            'success': False,
            'error': error_msg,
            'error_type': str(type(e)),
            'error_details': repr(e),
            'resource_groups': [],
            'count': 0
        }), 500

@azure_test_bp.route('/delete-resource-group', methods=['DELETE'])
def delete_resource_group():
    """Deleta um Resource Group"""
    try:
        if 'user_id' not in session:
            return jsonify({'error': 'Usuário não autenticado'}), 401
        
        user_id = session['user_id']
        data = request.get_json() or {}
        
        rg_name = data.get('name')
        if not rg_name:
            return jsonify({'error': 'Nome do Resource Group é obrigatório'}), 400
        
        logger.info(f"Deletando Resource Group '{rg_name}' para usuário {user_id}")
        
        # Obter credenciais
        if not azure_auth_service.is_user_authenticated(user_id):
            return jsonify({'error': 'Credenciais Azure não configuradas'}), 400
        
        creds = azure_auth_service.get_user_credentials(user_id)
        
        # Criar cliente
        credential = ClientSecretCredential(
            tenant_id=creds.tenant_id,
            client_id=creds.client_id,
            client_secret=creds.get_client_secret()
        )
        
        resource_client = ResourceManagementClient(credential, creds.subscription_id)
        
        # Deletar Resource Group (operação assíncrona)
        delete_operation = resource_client.resource_groups.begin_delete(rg_name)
        
        logger.info(f"Operação de deleção iniciada para '{rg_name}'")
        
        return jsonify({
            'success': True,
            'message': f'Deleção do Resource Group "{rg_name}" iniciada',
            'operation_status': 'in_progress'
        }), 200
        
    except Exception as e:
        error_msg = f"Erro ao deletar Resource Group: {str(e)}"
        logger.error(error_msg)
        return jsonify({
            'success': False,
            'error': error_msg
        }), 500



@azure_test_bp.route('/create-resource-group', methods=['POST'])
def create_resource_group():
    """Cria um novo Resource Group"""
    try:
        if 'user_id' not in session:
            return jsonify({'error': 'Usuário não autenticado'}), 401
        
        user_id = session['user_id']
        data = request.get_json() or {}
        
        rg_name = data.get('name')
        location = data.get('location', 'East US')
        
        if not rg_name:
            return jsonify({'error': 'Nome do Resource Group é obrigatório'}), 400
        
        logger.info(f"Criando Resource Group '{rg_name}' em '{location}' para usuário {user_id}")
        
        # Obter credenciais
        if not azure_auth_service.is_user_authenticated(user_id):
            return jsonify({'error': 'Credenciais Azure não configuradas'}), 400
        
        creds = azure_auth_service.get_user_credentials(user_id)
        
        # Criar cliente
        credential = ClientSecretCredential(
            tenant_id=creds.tenant_id,
            client_id=creds.client_id,
            client_secret=creds.get_client_secret()
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
        
        result = resource_client.resource_groups.create_or_update(rg_name, rg_params)
        
        logger.info(f"Resource Group '{rg_name}' criado com sucesso")
        
        return jsonify({
            'success': True,
            'message': f'Resource Group "{rg_name}" criado com sucesso',
            'resource_group': {
                'name': result.name,
                'location': result.location,
                'id': result.id,
                'tags': result.tags or {}
            }
        }), 200
        
    except Exception as e:
        error_msg = f"Erro ao criar Resource Group: {str(e)}"
        logger.error(error_msg)
        return jsonify({
            'success': False,
            'error': error_msg
        }), 500

