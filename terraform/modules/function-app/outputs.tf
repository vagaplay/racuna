# Outputs do módulo Function App

output "function_app_name" {
  description = "Nome do Function App"
  value       = azurerm_linux_function_app.main.name
}

output "function_app_id" {
  description = "ID do Function App"
  value       = azurerm_linux_function_app.main.id
}

output "function_app_url" {
  description = "URL do Function App"
  value       = "https://${azurerm_linux_function_app.main.default_hostname}"
}

output "function_app_default_hostname" {
  description = "Hostname padrão do Function App"
  value       = azurerm_linux_function_app.main.default_hostname
}

output "function_app_principal_id" {
  description = "Principal ID da identidade gerenciada do Function App"
  value       = azurerm_linux_function_app.main.identity[0].principal_id
}

output "function_app_tenant_id" {
  description = "Tenant ID da identidade gerenciada do Function App"
  value       = azurerm_linux_function_app.main.identity[0].tenant_id
}

output "function_service_plan_id" {
  description = "ID do Service Plan do Function App"
  value       = azurerm_service_plan.function_plan.id
}

output "function_service_plan_name" {
  description = "Nome do Service Plan do Function App"
  value       = azurerm_service_plan.function_plan.name
}

# Outputs do slot de staging
output "function_app_staging_url" {
  description = "URL do slot de staging do Function App"
  value       = "https://${azurerm_linux_function_app_slot.staging.default_hostname}"
}

output "function_app_staging_hostname" {
  description = "Hostname do slot de staging do Function App"
  value       = azurerm_linux_function_app_slot.staging.default_hostname
}

# Outputs para configuração de CI/CD
output "function_app_publish_profile" {
  description = "Perfil de publicação do Function App"
  value       = azurerm_linux_function_app.main.site_credential
  sensitive   = true
}

output "function_app_staging_publish_profile" {
  description = "Perfil de publicação do slot de staging do Function App"
  value       = azurerm_linux_function_app_slot.staging.site_credential
  sensitive   = true
}

# Outputs para monitoramento
output "function_app_outbound_ip_addresses" {
  description = "Endereços IP de saída do Function App"
  value       = azurerm_linux_function_app.main.outbound_ip_addresses
}

output "function_app_possible_outbound_ip_addresses" {
  description = "Possíveis endereços IP de saída do Function App"
  value       = azurerm_linux_function_app.main.possible_outbound_ip_addresses
}

# Outputs para configuração de segurança
output "function_app_kind" {
  description = "Tipo do Function App"
  value       = azurerm_linux_function_app.main.kind
}

output "function_app_custom_domain_verification_id" {
  description = "ID de verificação de domínio customizado do Function App"
  value       = azurerm_linux_function_app.main.custom_domain_verification_id
}

