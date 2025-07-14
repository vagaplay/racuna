# Outputs do Terraform para o projeto BOLT
# Estes valores serão úteis para as pipelines de CI/CD e configuração

output "resource_group_name" {
  description = "Nome do Resource Group criado"
  value       = azurerm_resource_group.main.name
}

output "resource_group_location" {
  description = "Localização do Resource Group"
  value       = azurerm_resource_group.main.location
}

output "frontend_app_name" {
  description = "Nome do App Service do frontend"
  value       = module.app_service.frontend_app_name
}

output "frontend_app_url" {
  description = "URL do frontend"
  value       = module.app_service.frontend_app_url
}

output "backend_app_name" {
  description = "Nome do App Service do backend"
  value       = module.app_service.backend_app_name
}

output "backend_app_url" {
  description = "URL do backend"
  value       = module.app_service.backend_app_url
}

output "function_app_name" {
  description = "Nome do Function App"
  value       = module.function_app.function_app_name
}

output "function_app_url" {
  description = "URL do Function App"
  value       = module.function_app.function_app_url
}

output "storage_account_name" {
  description = "Nome da Storage Account"
  value       = module.storage.storage_account_name
}

output "storage_account_primary_endpoint" {
  description = "Endpoint primário da Storage Account"
  value       = module.storage.storage_account_primary_endpoint
}

output "application_insights_name" {
  description = "Nome do Application Insights"
  value       = azurerm_application_insights.main.name
}

output "application_insights_instrumentation_key" {
  description = "Chave de instrumentação do Application Insights"
  value       = azurerm_application_insights.main.instrumentation_key
  sensitive   = true
}

output "application_insights_connection_string" {
  description = "String de conexão do Application Insights"
  value       = azurerm_application_insights.main.connection_string
  sensitive   = true
}

output "app_service_plan_name" {
  description = "Nome do App Service Plan"
  value       = module.app_service.app_service_plan_name
}

output "deployment_summary" {
  description = "Resumo do deployment"
  value = {
    project_name        = "BOLT"
    environment        = var.environment
    resource_group     = azurerm_resource_group.main.name
    location          = azurerm_resource_group.main.location
    frontend_url      = module.app_service.frontend_app_url
    backend_url       = module.app_service.backend_app_url
    function_app_url  = module.function_app.function_app_url
    created_at        = timestamp()
  }
}

# Outputs para configuração das pipelines de CI/CD
output "pipeline_variables" {
  description = "Variáveis para configuração das pipelines"
  value = {
    AZURE_RESOURCE_GROUP     = azurerm_resource_group.main.name
    AZURE_LOCATION          = azurerm_resource_group.main.location
    FRONTEND_APP_NAME       = module.app_service.frontend_app_name
    BACKEND_APP_NAME        = module.app_service.backend_app_name
    FUNCTION_APP_NAME       = module.function_app.function_app_name
    STORAGE_ACCOUNT_NAME    = module.storage.storage_account_name
    APP_SERVICE_PLAN_NAME   = module.app_service.app_service_plan_name
  }
}

# Outputs para configuração de ambiente
output "environment_variables" {
  description = "Variáveis de ambiente para as aplicações"
  value = {
    REACT_APP_API_BASE_URL           = module.app_service.backend_app_url
    FLASK_ENV                        = var.environment
    APPLICATIONINSIGHTS_CONNECTION_STRING = azurerm_application_insights.main.connection_string
    AZURE_STORAGE_CONNECTION_STRING  = module.storage.storage_connection_string
    FUNCTIONS_WORKER_RUNTIME         = var.function_app_runtime
  }
  sensitive = true
}

# Outputs para monitoramento
output "monitoring_endpoints" {
  description = "Endpoints para monitoramento"
  value = {
    frontend_health_check  = "${module.app_service.frontend_app_url}/health"
    backend_health_check   = "${module.app_service.backend_app_url}/health"
    function_app_status    = "${module.function_app.function_app_url}/api/status"
    application_insights   = "https://portal.azure.com/#@${var.azure_tenant_id}/resource${azurerm_application_insights.main.id}"
  }
}

# Output para configuração de DNS (se domínio customizado for usado)
output "dns_configuration" {
  description = "Configuração de DNS para domínio customizado"
  value = var.enable_custom_domain ? {
    custom_domain     = var.custom_domain_name
    cname_target     = module.app_service.frontend_app_default_hostname
    txt_verification = module.app_service.frontend_domain_verification_id
  } : null
}

