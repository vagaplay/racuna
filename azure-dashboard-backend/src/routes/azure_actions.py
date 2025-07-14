"""
Rotas para ações reais no Azure
Endpoints que executam operações reais na subscription Azure
"""

from flask import Blueprint, request, jsonify, session
from src.services.azure_actions_service import azure_actions_service
import logging

logger = logging.getLogger(__name__)

azure_actions_bp = Blueprint('azure_actions', __name__)

@azure_actions_bp.route('/create-lock', methods=['POST'])
def create_subscription_lock():
    """Cria um lock de prevenção na subscription ou resource group"""
    try:
        if 'user_id' not in session:
            return jsonify({'error': 'Usuário não autenticado'}), 401
        
        user_id = session['user_id']
        data = request.get_json() or {}
        
        # Parâmetros do lock
        lock_name = data.get('lock_name', 'Prevent-Spending-BudgetControl')
        level = data.get('level', 'CanNotDelete')
        resource_group = data.get('resource_group')  # None = subscription
        notes = data.get('notes')
        
        logger.info(f"Usuário {user_id} criando lock '{lock_name}' com nível '{level}'")
        if resource_group:
            logger.info(f"Escopo: Resource Group '{resource_group}'")
        else:
            logger.info(f"Escopo: Subscription")
        
        # Usar método flexível do serviço
        if resource_group:
            # Criar lock no Resource Group
            result = azure_actions_service.create_resource_group_lock(user_id, lock_name, resource_group, level, notes)
        else:
            # Criar lock na Subscription (método existente)
            result = azure_actions_service.create_subscription_lock(user_id, lock_name, level, notes)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"Erro ao criar lock: {str(e)}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

@azure_actions_bp.route('/remove-lock', methods=['DELETE'])
def remove_subscription_lock():
    """Remove um lock da subscription"""
    try:
        if 'user_id' not in session:
            return jsonify({'error': 'Usuário não autenticado'}), 401
        
        user_id = session['user_id']
        data = request.get_json() or {}
        
        # Nome do lock (padrão ou customizado)
        lock_name = data.get('lock_name', 'Prevent-Spending-BudgetControl')
        
        result = azure_actions_service.remove_subscription_lock(user_id, lock_name)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"Erro ao remover lock: {str(e)}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

@azure_actions_bp.route('/list-locks', methods=['GET'])
def list_subscription_locks():
    """Lista todos os locks da subscription"""
    try:
        if 'user_id' not in session:
            return jsonify({'error': 'Usuário não autenticado'}), 401
        
        user_id = session['user_id']
        
        result = azure_actions_service.list_subscription_locks(user_id)
        
        return jsonify(result), 200
            
    except Exception as e:
        logger.error(f"Erro ao listar locks: {str(e)}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

@azure_actions_bp.route('/list-vms', methods=['GET'])
def list_virtual_machines():
    """Lista todas as VMs da subscription"""
    try:
        if 'user_id' not in session:
            return jsonify({'error': 'Usuário não autenticado'}), 401
        
        user_id = session['user_id']
        
        result = azure_actions_service.list_virtual_machines(user_id)
        
        return jsonify(result), 200
            
    except Exception as e:
        logger.error(f"Erro ao listar VMs: {str(e)}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

@azure_actions_bp.route('/vm-action', methods=['POST'])
def vm_action():
    """Executa ação em uma VM (start/stop)"""
    try:
        if 'user_id' not in session:
            return jsonify({'error': 'Usuário não autenticado'}), 401
        
        user_id = session['user_id']
        data = request.get_json()
        
        # Validar dados obrigatórios
        required_fields = ['action', 'resource_group', 'vm_name']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'Campo obrigatório: {field}'}), 400
        
        action = data['action']
        resource_group = data['resource_group']
        vm_name = data['vm_name']
        
        if action == 'start':
            result = azure_actions_service.start_virtual_machine(user_id, resource_group, vm_name)
        elif action == 'shutdown':
            result = azure_actions_service.shutdown_virtual_machine(user_id, resource_group, vm_name)
        else:
            return jsonify({'error': 'Ação inválida. Use "start" ou "shutdown"'}), 400
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"Erro ao executar ação na VM: {str(e)}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

@azure_actions_bp.route('/apply-tags', methods=['POST'])
def apply_tags():
    """Aplica tags a um recurso"""
    try:
        if 'user_id' not in session:
            return jsonify({'error': 'Usuário não autenticado'}), 401
        
        user_id = session['user_id']
        data = request.get_json()
        
        # Validar dados obrigatórios
        required_fields = ['resource_id', 'tags']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'Campo obrigatório: {field}'}), 400
        
        resource_id = data['resource_id']
        tags = data['tags']
        
        if not isinstance(tags, dict):
            return jsonify({'error': 'Tags devem ser um objeto/dicionário'}), 400
        
        result = azure_actions_service.apply_tags_to_resource(user_id, resource_id, tags)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"Erro ao aplicar tags: {str(e)}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

@azure_actions_bp.route('/bulk-shutdown-vms', methods=['POST'])
def bulk_shutdown_vms():
    """Desliga múltiplas VMs de uma vez"""
    try:
        if 'user_id' not in session:
            return jsonify({'error': 'Usuário não autenticado'}), 401
        
        user_id = session['user_id']
        data = request.get_json() or {}
        
        # Filtros opcionais
        exclude_tags = data.get('exclude_tags', {})  # VMs com essas tags não serão desligadas
        include_only_tags = data.get('include_only_tags', {})  # Apenas VMs com essas tags
        
        # Listar VMs primeiro
        vms_result = azure_actions_service.list_virtual_machines(user_id)
        
        if not vms_result['success']:
            return jsonify(vms_result), 400
        
        vms_to_shutdown = []
        results = []
        
        for vm in vms_result['vms']:
            # Verificar se VM está ligada
            if vm['power_state'] != 'running':
                continue
            
            # Aplicar filtros de tags
            vm_tags = vm.get('tags', {})
            
            # Se include_only_tags especificado, VM deve ter todas essas tags
            if include_only_tags:
                if not all(vm_tags.get(k) == v for k, v in include_only_tags.items()):
                    continue
            
            # Se exclude_tags especificado, VM não deve ter nenhuma dessas tags
            if exclude_tags:
                if any(vm_tags.get(k) == v for k, v in exclude_tags.items()):
                    continue
            
            # Desligar VM
            shutdown_result = azure_actions_service.shutdown_virtual_machine(
                user_id, vm['resource_group'], vm['name']
            )
            
            results.append({
                'vm_name': vm['name'],
                'resource_group': vm['resource_group'],
                'success': shutdown_result['success'],
                'message': shutdown_result.get('message', shutdown_result.get('error'))
            })
            
            if shutdown_result['success']:
                vms_to_shutdown.append(vm['name'])
        
        return jsonify({
            'success': True,
            'message': f'{len(vms_to_shutdown)} VMs processadas para shutdown',
            'shutdown_vms': vms_to_shutdown,
            'detailed_results': results
        }), 200
            
    except Exception as e:
        logger.error(f"Erro no shutdown em massa: {str(e)}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

@azure_actions_bp.route('/test', methods=['GET'])
def test_actions():
    """Endpoint de teste para ações Azure"""
    if 'user_id' not in session:
        return jsonify({'error': 'Usuário não autenticado'}), 401
    
    return jsonify({
        'success': True,
        'message': 'Azure Actions API funcionando',
        'user_id': session['user_id'],
        'available_actions': [
            'create-lock',
            'remove-lock', 
            'list-locks',
            'list-vms',
            'vm-action',
            'apply-tags',
            'bulk-shutdown-vms'
        ]
    }), 200

