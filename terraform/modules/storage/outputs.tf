# Outputs do módulo Storage

output "storage_account_name" {
  description = "Nome da Storage Account"
  value       = azurerm_storage_account.main.name
}

output "storage_account_id" {
  description = "ID da Storage Account"
  value       = azurerm_storage_account.main.id
}

output "storage_account_primary_endpoint" {
  description = "Endpoint primário da Storage Account"
  value       = azurerm_storage_account.main.primary_blob_endpoint
}

output "storage_account_access_key" {
  description = "Chave de acesso primária da Storage Account"
  value       = azurerm_storage_account.main.primary_access_key
  sensitive   = true
}

output "storage_connection_string" {
  description = "String de conexão da Storage Account"
  value       = azurerm_storage_account.main.primary_connection_string
  sensitive   = true
}

output "frontend_assets_container_url" {
  description = "URL do container de assets do frontend"
  value       = "${azurerm_storage_account.main.primary_blob_endpoint}${azurerm_storage_container.frontend_assets.name}"
}

output "logs_container_name" {
  description = "Nome do container de logs"
  value       = azurerm_storage_container.logs.name
}

output "app_data_container_name" {
  description = "Nome do container de dados da aplicação"
  value       = azurerm_storage_container.app_data.name
}

output "shared_files_url" {
  description = "URL do File Share"
  value       = azurerm_storage_share.shared_files.url
}

output "task_queue_name" {
  description = "Nome da fila de tarefas"
  value       = azurerm_storage_queue.task_queue.name
}

output "app_config_table_name" {
  description = "Nome da tabela de configuração"
  value       = azurerm_storage_table.app_config.name
}

