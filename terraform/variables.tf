# Variables for BOLT Dashboard Terraform deployment

variable "app_name" {
  description = "Nome base da aplicação"
  type        = string
  default     = "bolt-dashboard"
}

variable "resource_group_name" {
  description = "Nome do Resource Group"
  type        = string
  default     = "rg-bolt-dashboard"
}

variable "location" {
  description = "Localização dos recursos Azure"
  type        = string
  default     = "Brazil South"
}

variable "environment" {
  description = "Ambiente (development, staging, production)"
  type        = string
  default     = "production"
  
  validation {
    condition     = contains(["development", "staging", "production"], var.environment)
    error_message = "Environment deve ser development, staging ou production."
  }
}

variable "app_service_sku" {
  description = "SKU do App Service Plan"
  type        = string
  default     = "B1"  # Basic tier - pode ser F1 (Free) para desenvolvimento
}

variable "static_web_app_sku" {
  description = "SKU do Static Web App"
  type        = string
  default     = "Free"  # Free tier disponível
}

variable "azure_client_id" {
  description = "Azure Client ID para autenticação"
  type        = string
  sensitive   = true
}

variable "azure_client_secret" {
  description = "Azure Client Secret para autenticação"
  type        = string
  sensitive   = true
}

variable "azure_tenant_id" {
  description = "Azure Tenant ID"
  type        = string
  sensitive   = true
}

variable "azure_subscription_id" {
  description = "Azure Subscription ID"
  type        = string
  sensitive   = true
}

variable "secret_key" {
  description = "Flask Secret Key"
  type        = string
  sensitive   = true
  default     = ""
}

variable "custom_domain" {
  description = "Domínio customizado (opcional)"
  type        = string
  default     = ""
}

variable "enable_backup" {
  description = "Habilitar backup automático"
  type        = bool
  default     = true
}

variable "backup_retention_days" {
  description = "Dias de retenção do backup"
  type        = number
  default     = 30
}

variable "enable_monitoring" {
  description = "Habilitar monitoramento avançado"
  type        = bool
  default     = true
}

variable "tags" {
  description = "Tags adicionais para recursos"
  type        = map(string)
  default     = {}
}

