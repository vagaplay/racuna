# Configuração para ambiente de produção

environment = "prod"
location    = "East US"

# SKU básico para produção (pode ser ajustado conforme necessidade)
app_service_sku = "B1"

# Configurações de monitoramento (habilitado para produção)
enable_application_insights = true
enable_monitoring          = true
log_retention_days         = 90

# Configurações de domínio customizado (configurar conforme necessário)
enable_custom_domain = false
# custom_domain_name = "dashboard.suaempresa.com"

# Configurações de backup (habilitado para produção)
enable_backup         = true
backup_retention_days = 30

# Configurações de SSL/TLS (mais restritivo em produção)
enable_ssl           = true
minimum_tls_version  = "1.2"

# Configurações das Azure Functions
function_app_runtime = "python"
function_app_version = "3.9"

# Origens permitidas para CORS (mais restritivo em produção)
allowed_origins = [
  "https://dashboard.suaempresa.com",
  "https://www.dashboard.suaempresa.com"
]

# Tags para ambiente de produção
resource_tags = {
  "Environment" = "Production"
  "CostCenter"  = "TI"
  "Owner"       = "Equipe DevOps"
  "Project"     = "BOLT Dashboard"
  "Criticality" = "High"
  "Backup"      = "Required"
}

