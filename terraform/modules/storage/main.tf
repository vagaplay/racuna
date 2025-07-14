# Módulo Storage Account para o projeto BOLT
# Responsável por criar e configurar a conta de armazenamento

variable "resource_group_name" {
  description = "Nome do Resource Group"
  type        = string
}

variable "location" {
  description = "Localização dos recursos"
  type        = string
}

variable "storage_account_name" {
  description = "Nome da Storage Account"
  type        = string
}

variable "tags" {
  description = "Tags para os recursos"
  type        = map(string)
  default     = {}
}

# Storage Account para Azure Functions e armazenamento geral
resource "azurerm_storage_account" "main" {
  name                     = var.storage_account_name
  resource_group_name      = var.resource_group_name
  location                = var.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
  
  # Configurações de segurança
  min_tls_version                = "TLS1_2"
  allow_nested_items_to_be_public = false
  
  # Habilitar HTTPS apenas
  enable_https_traffic_only = true
  
  # Configurações de blob
  blob_properties {
    delete_retention_policy {
      days = 7
    }
    container_delete_retention_policy {
      days = 7
    }
  }
  
  tags = var.tags
}

# Container para armazenar arquivos estáticos do frontend (se necessário)
resource "azurerm_storage_container" "frontend_assets" {
  name                  = "frontend-assets"
  storage_account_name  = azurerm_storage_account.main.name
  container_access_type = "blob"
}

# Container para logs e backups
resource "azurerm_storage_container" "logs" {
  name                  = "logs"
  storage_account_name  = azurerm_storage_account.main.name
  container_access_type = "private"
}

# Container para dados de aplicação (se necessário)
resource "azurerm_storage_container" "app_data" {
  name                  = "app-data"
  storage_account_name  = azurerm_storage_account.main.name
  container_access_type = "private"
}

# File Share para compartilhamento de arquivos entre serviços
resource "azurerm_storage_share" "shared_files" {
  name                 = "shared-files"
  storage_account_name = azurerm_storage_account.main.name
  quota                = 5  # 5 GB
}

# Queue para processamento assíncrono (se necessário)
resource "azurerm_storage_queue" "task_queue" {
  name                 = "task-queue"
  storage_account_name = azurerm_storage_account.main.name
}

# Table para armazenamento de dados estruturados simples
resource "azurerm_storage_table" "app_config" {
  name                 = "appconfig"
  storage_account_name = azurerm_storage_account.main.name
}

