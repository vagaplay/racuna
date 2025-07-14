# Configuração para ambiente de desenvolvimento

environment = "dev"
location    = "East US"

# SKU gratuito para desenvolvimento
app_service_sku = "F1"

# Configurações de monitoramento
enable_application_insights = true
enable_monitoring          = true
log_retention_days         = 30

# Configurações de domínio (não usar domínio customizado em dev)
enable_custom_domain = false

# Configurações de backup (desabilitado em dev)
enable_backup         = false
backup_retention_days = 7

# Configurações de SSL/TLS
enable_ssl           = true
minimum_tls_version  = "1.2"

# Configurações das Azure Functions
function_app_runtime = "python"
function_app_version = "3.9"

# Origens permitidas para CORS (mais permissivo em dev)
allowed_origins = ["*"]

# Tags para ambiente de desenvolvimento
resource_tags = {
  "Environment" = "Development"
  "CostCenter"  = "TI"
  "Owner"       = "Equipe DevOps"
  "Project"     = "BOLT Dashboard"
  "AutoShutdown" = "true"  # Para economizar custos
}

