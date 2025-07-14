    def create_flexible_lock(self, user_id: int, lock_name: str, level: str = "CanNotDelete", 
                           resource_group: str = None, notes: str = None) -> Dict[str, Any]:
        """Cria um lock na subscription ou resource group específico"""
        try:
            clients = self._get_clients(user_id)
            lock_client = clients['lock_client']
            
            # Parâmetros do lock
            lock_params = {
                'level': level,
                'notes': notes or f"Lock criado pelo BOLT Dashboard - {datetime.utcnow().isoformat()}"
            }
            
            logger.info(f"Criando lock '{lock_name}' com nível '{level}'")
            
            if resource_group:
                # Criar lock no Resource Group
                logger.info(f"Criando lock no Resource Group: {resource_group}")
                result = lock_client.management_locks.create_or_update_at_resource_group_level(
                    resource_group_name=resource_group,
                    lock_name=lock_name,
                    parameters=lock_params
                )
                scope_info = f"Resource Group '{resource_group}'"
            else:
                # Criar lock na Subscription
                logger.info(f"Criando lock na Subscription")
                result = lock_client.management_locks.create_or_update_at_subscription_level(
                    lock_name=lock_name,
                    parameters=lock_params
                )
                scope_info = "Subscription"
            
            logger.info(f"Lock '{lock_name}' criado com sucesso em {scope_info}")
            
            return {
                'success': True,
                'message': f'Lock "{lock_name}" criado com sucesso em {scope_info}',
                'lock_name': result.name,
                'level': result.level,
                'scope': scope_info,
                'notes': result.notes,
                'id': result.id
            }
            
        except HttpResponseError as e:
            if e.status_code == 409:
                return {
                    'success': False,
                    'error': f'Lock "{lock_name}" já existe'
                }
            else:
                error_msg = f"Erro HTTP ao criar lock: {e.message}"
                logger.error(error_msg)
                return {
                    'success': False,
                    'error': error_msg
                }
        except Exception as e:
            error_msg = f"Erro ao criar lock: {str(e)}"
            logger.error(error_msg)
            logger.error(f"Detalhes: {repr(e)}")
            return {
                'success': False,
                'error': error_msg
            }

