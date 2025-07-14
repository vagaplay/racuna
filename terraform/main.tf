# Terraform Configuration for Azure BOLT Dashboard
# Deploy completo para produção no Azure

terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~>3.0"
    }
  }
}

provider "azurerm" {
  features {}
}

# Resource Group
resource "azurerm_resource_group" "bolt_dashboard" {
  name     = var.resource_group_name
  location = var.location

  tags = {
    Environment = var.environment
    Project     = "BOLT-Dashboard"
    ManagedBy   = "Terraform"
  }
}

# App Service Plan
resource "azurerm_service_plan" "bolt_dashboard" {
  name                = "${var.app_name}-plan"
  resource_group_name = azurerm_resource_group.bolt_dashboard.name
  location           = azurerm_resource_group.bolt_dashboard.location
  os_type            = "Linux"
  sku_name           = var.app_service_sku

  tags = {
    Environment = var.environment
    Project     = "BOLT-Dashboard"
  }
}

# App Service para Backend
resource "azurerm_linux_web_app" "bolt_backend" {
  name                = "${var.app_name}-backend"
  resource_group_name = azurerm_resource_group.bolt_dashboard.name
  location           = azurerm_resource_group.bolt_dashboard.location
  service_plan_id    = azurerm_service_plan.bolt_dashboard.id

  site_config {
    application_stack {
      python_version = "3.11"
    }
    
    always_on = var.environment == "production" ? true : false
    
    cors {
      allowed_origins = [
        "https://${var.app_name}-frontend.azurestaticapps.net",
        var.custom_domain != "" ? "https://${var.custom_domain}" : ""
      ]
      support_credentials = true
    }
  }

  app_settings = {
    "FLASK_ENV"                = var.environment
    "SECRET_KEY"              = var.secret_key
    "AZURE_CLIENT_ID"         = var.azure_client_id
    "AZURE_CLIENT_SECRET"     = var.azure_client_secret
    "AZURE_TENANT_ID"         = var.azure_tenant_id
    "AZURE_SUBSCRIPTION_ID"   = var.azure_subscription_id
    "DATABASE_URL"            = "sqlite:///app.db"
    "CORS_ORIGINS"            = "https://${var.app_name}-frontend.azurestaticapps.net"
  }

  tags = {
    Environment = var.environment
    Project     = "BOLT-Dashboard"
  }
}

# Static Web App para Frontend
resource "azurerm_static_site" "bolt_frontend" {
  name                = "${var.app_name}-frontend"
  resource_group_name = azurerm_resource_group.bolt_dashboard.name
  location           = "West Europe"  # Static Web Apps só disponível em certas regiões
  sku_tier           = var.static_web_app_sku

  tags = {
    Environment = var.environment
    Project     = "BOLT-Dashboard"
  }
}

# Key Vault para secrets
resource "azurerm_key_vault" "bolt_dashboard" {
  name                = "${var.app_name}-kv-${random_string.suffix.result}"
  location           = azurerm_resource_group.bolt_dashboard.location
  resource_group_name = azurerm_resource_group.bolt_dashboard.name
  tenant_id          = data.azurerm_client_config.current.tenant_id
  sku_name           = "standard"

  access_policy {
    tenant_id = data.azurerm_client_config.current.tenant_id
    object_id = data.azurerm_client_config.current.object_id

    secret_permissions = [
      "Get",
      "List",
      "Set",
      "Delete",
      "Recover",
      "Backup",
      "Restore"
    ]
  }

  # Acesso para o App Service
  access_policy {
    tenant_id = data.azurerm_client_config.current.tenant_id
    object_id = azurerm_linux_web_app.bolt_backend.identity[0].principal_id

    secret_permissions = [
      "Get",
      "List"
    ]
  }

  tags = {
    Environment = var.environment
    Project     = "BOLT-Dashboard"
  }
}

# Secrets no Key Vault
resource "azurerm_key_vault_secret" "azure_client_secret" {
  name         = "azure-client-secret"
  value        = var.azure_client_secret
  key_vault_id = azurerm_key_vault.bolt_dashboard.id
}

resource "azurerm_key_vault_secret" "secret_key" {
  name         = "flask-secret-key"
  value        = var.secret_key
  key_vault_id = azurerm_key_vault.bolt_dashboard.id
}

# Application Insights
resource "azurerm_application_insights" "bolt_dashboard" {
  name                = "${var.app_name}-insights"
  location           = azurerm_resource_group.bolt_dashboard.location
  resource_group_name = azurerm_resource_group.bolt_dashboard.name
  application_type   = "web"

  tags = {
    Environment = var.environment
    Project     = "BOLT-Dashboard"
  }
}

# Storage Account para logs e backups
resource "azurerm_storage_account" "bolt_dashboard" {
  name                     = "${replace(var.app_name, "-", "")}storage${random_string.suffix.result}"
  resource_group_name      = azurerm_resource_group.bolt_dashboard.name
  location                = azurerm_resource_group.bolt_dashboard.location
  account_tier            = "Standard"
  account_replication_type = "LRS"

  tags = {
    Environment = var.environment
    Project     = "BOLT-Dashboard"
  }
}

# Container para backups
resource "azurerm_storage_container" "backups" {
  name                  = "backups"
  storage_account_name  = azurerm_storage_account.bolt_dashboard.name
  container_access_type = "private"
}

# Function App para Azure Functions
resource "azurerm_linux_function_app" "bolt_functions" {
  name                = "${var.app_name}-functions"
  resource_group_name = azurerm_resource_group.bolt_dashboard.name
  location           = azurerm_resource_group.bolt_dashboard.location
  service_plan_id    = azurerm_service_plan.bolt_dashboard.id
  storage_account_name = azurerm_storage_account.bolt_dashboard.name
  storage_account_access_key = azurerm_storage_account.bolt_dashboard.primary_access_key

  site_config {
    application_stack {
      python_version = "3.11"
    }
  }

  app_settings = {
    "AZURE_CLIENT_ID"         = var.azure_client_id
    "AZURE_CLIENT_SECRET"     = var.azure_client_secret
    "AZURE_TENANT_ID"         = var.azure_tenant_id
    "AZURE_SUBSCRIPTION_ID"   = var.azure_subscription_id
    "APPINSIGHTS_INSTRUMENTATIONKEY" = azurerm_application_insights.bolt_dashboard.instrumentation_key
  }

  tags = {
    Environment = var.environment
    Project     = "BOLT-Dashboard"
  }
}

# Log Analytics Workspace
resource "azurerm_log_analytics_workspace" "bolt_dashboard" {
  name                = "${var.app_name}-logs"
  location           = azurerm_resource_group.bolt_dashboard.location
  resource_group_name = azurerm_resource_group.bolt_dashboard.name
  sku                = "PerGB2018"
  retention_in_days  = 30

  tags = {
    Environment = var.environment
    Project     = "BOLT-Dashboard"
  }
}

# Random string para nomes únicos
resource "random_string" "suffix" {
  length  = 6
  special = false
  upper   = false
}

# Data sources
data "azurerm_client_config" "current" {}

# Outputs
output "backend_url" {
  value = "https://${azurerm_linux_web_app.bolt_backend.default_hostname}"
}

output "frontend_url" {
  value = "https://${azurerm_static_site.bolt_frontend.default_host_name}"
}

output "resource_group_name" {
  value = azurerm_resource_group.bolt_dashboard.name
}

output "key_vault_name" {
  value = azurerm_key_vault.bolt_dashboard.name
}

output "storage_account_name" {
  value = azurerm_storage_account.bolt_dashboard.name
}

output "function_app_name" {
  value = azurerm_linux_function_app.bolt_functions.name
}

