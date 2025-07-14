# Módulo App Service para o projeto BOLT
# Responsável por criar e configurar os App Services para frontend e backend

variable "resource_group_name" {
  description = "Nome do Resource Group"
  type        = string
}

variable "location" {
  description = "Localização dos recursos"
  type        = string
}

variable "app_service_plan_name" {
  description = "Nome do App Service Plan"
  type        = string
}

variable "frontend_app_name" {
  description = "Nome do App Service do frontend"
  type        = string
}

variable "backend_app_name" {
  description = "Nome do App Service do backend"
  type        = string
}

variable "application_insights_key" {
  description = "Chave do Application Insights"
  type        = string
}

variable "sku_name" {
  description = "SKU do App Service Plan"
  type        = string
  default     = "F1"
}

variable "tags" {
  description = "Tags para os recursos"
  type        = map(string)
  default     = {}
}

# App Service Plan
resource "azurerm_service_plan" "main" {
  name                = var.app_service_plan_name
  resource_group_name = var.resource_group_name
  location            = var.location
  os_type             = "Linux"
  sku_name            = var.sku_name
  
  tags = var.tags
}

# App Service para o Frontend (React)
resource "azurerm_linux_web_app" "frontend" {
  name                = var.frontend_app_name
  resource_group_name = var.resource_group_name
  location            = var.location
  service_plan_id     = azurerm_service_plan.main.id
  
  site_config {
    always_on = var.sku_name != "F1" ? true : false
    
    application_stack {
      node_version = "18-lts"
    }
    
    # Configurações de CORS
    cors {
      allowed_origins = ["*"]
      support_credentials = false
    }
  }
  
  app_settings = {
    "WEBSITE_NODE_DEFAULT_VERSION" = "18.17.0"
    "SCM_DO_BUILD_DURING_DEPLOYMENT" = "true"
    "APPINSIGHTS_INSTRUMENTATIONKEY" = var.application_insights_key
    "APPLICATIONINSIGHTS_CONNECTION_STRING" = "InstrumentationKey=${var.application_insights_key}"
    "ApplicationInsightsAgent_EXTENSION_VERSION" = "~3"
    "XDT_MicrosoftApplicationInsights_Mode" = "Recommended"
    "XDT_MicrosoftApplicationInsights_PreemptSdk" = "Disabled"
  }
  
  # Configurações de logs
  logs {
    detailed_error_messages = true
    failed_request_tracing  = true
    
    http_logs {
      file_system {
        retention_in_days = 7
        retention_in_mb   = 35
      }
    }
  }
  
  tags = var.tags
}

# App Service para o Backend (Flask)
resource "azurerm_linux_web_app" "backend" {
  name                = var.backend_app_name
  resource_group_name = var.resource_group_name
  location            = var.location
  service_plan_id     = azurerm_service_plan.main.id
  
  site_config {
    always_on = var.sku_name != "F1" ? true : false
    
    application_stack {
      python_version = "3.9"
    }
    
    # Configurações de CORS
    cors {
      allowed_origins = ["*"]
      support_credentials = false
    }
  }
  
  app_settings = {
    "FLASK_ENV" = "production"
    "FLASK_APP" = "src.main:app"
    "SCM_DO_BUILD_DURING_DEPLOYMENT" = "true"
    "APPINSIGHTS_INSTRUMENTATIONKEY" = var.application_insights_key
    "APPLICATIONINSIGHTS_CONNECTION_STRING" = "InstrumentationKey=${var.application_insights_key}"
    "ApplicationInsightsAgent_EXTENSION_VERSION" = "~3"
    "XDT_MicrosoftApplicationInsights_Mode" = "Recommended"
    "XDT_MicrosoftApplicationInsights_PreemptSdk" = "Disabled"
    
    # Configurações específicas do Flask
    "PYTHONPATH" = "/home/site/wwwroot"
    "WEBSITES_ENABLE_APP_SERVICE_STORAGE" = "false"
  }
  
  # Configurações de logs
  logs {
    detailed_error_messages = true
    failed_request_tracing  = true
    
    http_logs {
      file_system {
        retention_in_days = 7
        retention_in_mb   = 35
      }
    }
  }
  
  tags = var.tags
}

# Configuração de deployment slots para staging (apenas para SKUs que suportam)
resource "azurerm_linux_web_app_slot" "frontend_staging" {
  count          = var.sku_name != "F1" && var.sku_name != "D1" ? 1 : 0
  name           = "staging"
  app_service_id = azurerm_linux_web_app.frontend.id
  
  site_config {
    application_stack {
      node_version = "18-lts"
    }
  }
  
  app_settings = azurerm_linux_web_app.frontend.app_settings
  
  tags = var.tags
}

resource "azurerm_linux_web_app_slot" "backend_staging" {
  count          = var.sku_name != "F1" && var.sku_name != "D1" ? 1 : 0
  name           = "staging"
  app_service_id = azurerm_linux_web_app.backend.id
  
  site_config {
    application_stack {
      python_version = "3.9"
    }
  }
  
  app_settings = azurerm_linux_web_app.backend.app_settings
  
  tags = var.tags
}

