# Outputs do módulo App Service

output "app_service_plan_name" {
  description = "Nome do App Service Plan"
  value       = azurerm_service_plan.main.name
}

output "app_service_plan_id" {
  description = "ID do App Service Plan"
  value       = azurerm_service_plan.main.id
}

output "frontend_app_name" {
  description = "Nome do App Service do frontend"
  value       = azurerm_linux_web_app.frontend.name
}

output "frontend_app_id" {
  description = "ID do App Service do frontend"
  value       = azurerm_linux_web_app.frontend.id
}

output "frontend_app_url" {
  description = "URL do frontend"
  value       = "https://${azurerm_linux_web_app.frontend.default_hostname}"
}

output "frontend_app_default_hostname" {
  description = "Hostname padrão do frontend"
  value       = azurerm_linux_web_app.frontend.default_hostname
}

output "frontend_domain_verification_id" {
  description = "ID de verificação de domínio do frontend"
  value       = azurerm_linux_web_app.frontend.custom_domain_verification_id
}

output "backend_app_name" {
  description = "Nome do App Service do backend"
  value       = azurerm_linux_web_app.backend.name
}

output "backend_app_id" {
  description = "ID do App Service do backend"
  value       = azurerm_linux_web_app.backend.id
}

output "backend_app_url" {
  description = "URL do backend"
  value       = "https://${azurerm_linux_web_app.backend.default_hostname}"
}

output "backend_app_default_hostname" {
  description = "Hostname padrão do backend"
  value       = azurerm_linux_web_app.backend.default_hostname
}

output "backend_domain_verification_id" {
  description = "ID de verificação de domínio do backend"
  value       = azurerm_linux_web_app.backend.custom_domain_verification_id
}

# Outputs dos slots de staging (se existirem)
output "frontend_staging_url" {
  description = "URL do slot de staging do frontend"
  value       = length(azurerm_linux_web_app_slot.frontend_staging) > 0 ? "https://${azurerm_linux_web_app_slot.frontend_staging[0].default_hostname}" : null
}

output "backend_staging_url" {
  description = "URL do slot de staging do backend"
  value       = length(azurerm_linux_web_app_slot.backend_staging) > 0 ? "https://${azurerm_linux_web_app_slot.backend_staging[0].default_hostname}" : null
}

# Outputs para configuração de CI/CD
output "frontend_publish_profile" {
  description = "Perfil de publicação do frontend"
  value       = azurerm_linux_web_app.frontend.site_credential
  sensitive   = true
}

output "backend_publish_profile" {
  description = "Perfil de publicação do backend"
  value       = azurerm_linux_web_app.backend.site_credential
  sensitive   = true
}

# Outputs para monitoramento
output "frontend_outbound_ip_addresses" {
  description = "Endereços IP de saída do frontend"
  value       = azurerm_linux_web_app.frontend.outbound_ip_addresses
}

output "backend_outbound_ip_addresses" {
  description = "Endereços IP de saída do backend"
  value       = azurerm_linux_web_app.backend.outbound_ip_addresses
}

