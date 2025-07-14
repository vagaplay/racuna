# Módulo Networking para o projeto BOLT
# Responsável por configurações de rede e segurança

variable "resource_group_name" {
  description = "Nome do Resource Group"
  type        = string
}

variable "location" {
  description = "Localização dos recursos"
  type        = string
}

variable "project_name" {
  description = "Nome do projeto"
  type        = string
}

variable "environment" {
  description = "Ambiente (dev, staging, prod)"
  type        = string
}

variable "tags" {
  description = "Tags para os recursos"
  type        = map(string)
  default     = {}
}

# Network Security Group para controle de acesso
resource "azurerm_network_security_group" "main" {
  name                = "${var.project_name}-${var.environment}-nsg"
  location            = var.location
  resource_group_name = var.resource_group_name
  
  # Regra para permitir HTTPS
  security_rule {
    name                       = "AllowHTTPS"
    priority                   = 1001
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_range     = "443"
    source_address_prefix      = "*"
    destination_address_prefix = "*"
  }
  
  # Regra para permitir HTTP (redirecionamento para HTTPS)
  security_rule {
    name                       = "AllowHTTP"
    priority                   = 1002
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_range     = "80"
    source_address_prefix      = "*"
    destination_address_prefix = "*"
  }
  
  # Regra para bloquear acesso direto a portas de desenvolvimento
  security_rule {
    name                       = "DenyDevPorts"
    priority                   = 1100
    direction                  = "Inbound"
    access                     = "Deny"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_ranges    = ["3000", "5000", "8000", "8080"]
    source_address_prefix      = "*"
    destination_address_prefix = "*"
  }
  
  tags = var.tags
}

# Virtual Network (para configurações avançadas futuras)
resource "azurerm_virtual_network" "main" {
  name                = "${var.project_name}-${var.environment}-vnet"
  address_space       = ["10.0.0.0/16"]
  location            = var.location
  resource_group_name = var.resource_group_name
  
  tags = var.tags
}

# Subnet para App Services
resource "azurerm_subnet" "app_services" {
  name                 = "app-services-subnet"
  resource_group_name  = var.resource_group_name
  virtual_network_name = azurerm_virtual_network.main.name
  address_prefixes     = ["10.0.1.0/24"]
  
  # Delegação para App Services
  delegation {
    name = "app-service-delegation"
    
    service_delegation {
      name    = "Microsoft.Web/serverFarms"
      actions = ["Microsoft.Network/virtualNetworks/subnets/action"]
    }
  }
}

# Subnet para Function Apps
resource "azurerm_subnet" "function_apps" {
  name                 = "function-apps-subnet"
  resource_group_name  = var.resource_group_name
  virtual_network_name = azurerm_virtual_network.main.name
  address_prefixes     = ["10.0.2.0/24"]
  
  # Delegação para Function Apps
  delegation {
    name = "function-app-delegation"
    
    service_delegation {
      name    = "Microsoft.Web/serverFarms"
      actions = ["Microsoft.Network/virtualNetworks/subnets/action"]
    }
  }
}

# Associação do NSG com as subnets
resource "azurerm_subnet_network_security_group_association" "app_services" {
  subnet_id                 = azurerm_subnet.app_services.id
  network_security_group_id = azurerm_network_security_group.main.id
}

resource "azurerm_subnet_network_security_group_association" "function_apps" {
  subnet_id                 = azurerm_subnet.function_apps.id
  network_security_group_id = azurerm_network_security_group.main.id
}

# Private DNS Zone para resolução interna (opcional)
resource "azurerm_private_dns_zone" "main" {
  name                = "${var.project_name}-${var.environment}.internal"
  resource_group_name = var.resource_group_name
  
  tags = var.tags
}

# Link da Private DNS Zone com a VNet
resource "azurerm_private_dns_zone_virtual_network_link" "main" {
  name                  = "${var.project_name}-${var.environment}-dns-link"
  resource_group_name   = var.resource_group_name
  private_dns_zone_name = azurerm_private_dns_zone.main.name
  virtual_network_id    = azurerm_virtual_network.main.id
  registration_enabled  = true
  
  tags = var.tags
}

