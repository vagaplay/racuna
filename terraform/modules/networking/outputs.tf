# Outputs do módulo Networking

output "virtual_network_id" {
  description = "ID da Virtual Network"
  value       = azurerm_virtual_network.main.id
}

output "virtual_network_name" {
  description = "Nome da Virtual Network"
  value       = azurerm_virtual_network.main.name
}

output "app_services_subnet_id" {
  description = "ID da subnet dos App Services"
  value       = azurerm_subnet.app_services.id
}

output "function_apps_subnet_id" {
  description = "ID da subnet dos Function Apps"
  value       = azurerm_subnet.function_apps.id
}

output "network_security_group_id" {
  description = "ID do Network Security Group"
  value       = azurerm_network_security_group.main.id
}

output "network_security_group_name" {
  description = "Nome do Network Security Group"
  value       = azurerm_network_security_group.main.name
}

output "private_dns_zone_id" {
  description = "ID da Private DNS Zone"
  value       = azurerm_private_dns_zone.main.id
}

output "private_dns_zone_name" {
  description = "Nome da Private DNS Zone"
  value       = azurerm_private_dns_zone.main.name
}

