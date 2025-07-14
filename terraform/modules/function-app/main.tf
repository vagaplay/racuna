# Módulo Function App para o projeto BOLT
# Responsável por criar e configurar o Azure Function App para tarefas automatizadas

variable "resource_group_name" {
  description = "Nome do Resource Group"
  type        = string
}

variable "location" {
  description = "Localização dos recursos"
  type        = string
}

variable "function_app_name" {
  description = "Nome do Function App"
  type        = string
}

variable "storage_account_name" {
  description = "Nome da Storage Account"
  type        = string
}

variable "storage_account_access_key" {
  description = "Chave de acesso da Storage Account"
  type        = string
  sensitive   = true
}

variable "application_insights_key" {
  description = "Chave do Application Insights"
  type        = string
}

variable "tags" {
  description = "Tags para os recursos"
  type        = map(string)
  default     = {}
}

# Service Plan para o Function App (Consumption Plan)
resource "azurerm_service_plan" "function_plan" {
  name                = "${var.function_app_name}-plan"
  resource_group_name = var.resource_group_name
  location            = var.location
  os_type             = "Linux"
  sku_name            = "Y1"  # Consumption Plan
  
  tags = var.tags
}

# Function App
resource "azurerm_linux_function_app" "main" {
  name                = var.function_app_name
  resource_group_name = var.resource_group_name
  location            = var.location
  service_plan_id     = azurerm_service_plan.function_plan.id
  
  storage_account_name       = var.storage_account_name
  storage_account_access_key = var.storage_account_access_key
  
  site_config {
    application_stack {
      python_version = "3.9"
    }
    
    # Configurações de CORS
    cors {
      allowed_origins = ["*"]
      support_credentials = false
    }
    
    # Configurações de runtime
    application_insights_key = var.application_insights_key
  }
  
  app_settings = {
    "FUNCTIONS_WORKER_RUNTIME" = "python"
    "FUNCTIONS_EXTENSION_VERSION" = "~4"
    "APPINSIGHTS_INSTRUMENTATIONKEY" = var.application_insights_key
    "APPLICATIONINSIGHTS_CONNECTION_STRING" = "InstrumentationKey=${var.application_insights_key}"
    
    # Configurações específicas para as funções BOLT
    "AZURE_CLIENT_ID" = ""  # Será configurado via pipeline
    "AZURE_CLIENT_SECRET" = ""  # Será configurado via pipeline
    "AZURE_TENANT_ID" = ""  # Será configurado via pipeline
    "AZURE_SUBSCRIPTION_ID" = ""  # Será configurado via pipeline
    
    # Configurações de timeout e performance
    "WEBSITE_RUN_FROM_PACKAGE" = "1"
    "WEBSITE_ENABLE_SYNC_UPDATE_SITE" = "true"
    "WEBSITE_TIME_ZONE" = "America/Sao_Paulo"
    
    # Configurações de logging
    "WEBSITE_HTTPLOGGING_RETENTION_DAYS" = "7"
    "FUNCTIONS_WORKER_PROCESS_COUNT" = "1"
    "PYTHON_THREADPOOL_THREAD_COUNT" = "1"
  }
  
  # Configurações de identidade gerenciada
  identity {
    type = "SystemAssigned"
  }
  
  tags = var.tags
}

# Configuração de deployment slot para staging (se necessário)
resource "azurerm_linux_function_app_slot" "staging" {
  name                 = "staging"
  function_app_id      = azurerm_linux_function_app.main.id
  storage_account_name = var.storage_account_name
  storage_account_access_key = var.storage_account_access_key
  
  site_config {
    application_stack {
      python_version = "3.9"
    }
    
    application_insights_key = var.application_insights_key
  }
  
  app_settings = azurerm_linux_function_app.main.app_settings
  
  tags = var.tags
}

