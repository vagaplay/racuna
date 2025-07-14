#!/bin/bash

# Sistema de Backup e Recuperação para BOLT Dashboard
# Faz backup do banco de dados e configurações

set -e

# Configurações
BACKUP_DIR="/home/ubuntu/azure-dashboard/backups"
DB_PATH="/home/ubuntu/azure-dashboard/azure-dashboard-backend/database.db"
CONFIG_DIR="/home/ubuntu/azure-dashboard/azure-dashboard-backend/src"
DATE=$(date +%Y%m%d_%H%M%S)
RETENTION_DAYS=30

# Cores para output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[WARNING] $1${NC}"
}

error() {
    echo -e "${RED}[ERROR] $1${NC}"
    exit 1
}

# Criar diretório de backup
create_backup_dir() {
    log "Criando diretório de backup..."
    mkdir -p "$BACKUP_DIR"
    mkdir -p "$BACKUP_DIR/database"
    mkdir -p "$BACKUP_DIR/config"
    mkdir -p "$BACKUP_DIR/logs"
}

# Backup do banco de dados
backup_database() {
    log "Fazendo backup do banco de dados..."
    
    if [ -f "$DB_PATH" ]; then
        cp "$DB_PATH" "$BACKUP_DIR/database/database_$DATE.db"
        
        # Criar dump SQL também
        sqlite3 "$DB_PATH" .dump > "$BACKUP_DIR/database/database_$DATE.sql"
        
        log "✅ Backup do banco de dados concluído"
    else
        warn "Banco de dados não encontrado em $DB_PATH"
    fi
}

# Backup das configurações
backup_config() {
    log "Fazendo backup das configurações..."
    
    # Backup dos arquivos de configuração (sem secrets)
    tar -czf "$BACKUP_DIR/config/config_$DATE.tar.gz" \
        --exclude="*.pyc" \
        --exclude="__pycache__" \
        --exclude="*.log" \
        --exclude=".env" \
        "$CONFIG_DIR"
    
    # Backup das Azure Functions
    if [ -d "/home/ubuntu/azure-dashboard/azure-functions-project" ]; then
        tar -czf "$BACKUP_DIR/config/functions_$DATE.tar.gz" \
            "/home/ubuntu/azure-dashboard/azure-functions-project"
    fi
    
    log "✅ Backup das configurações concluído"
}

# Backup dos logs
backup_logs() {
    log "Fazendo backup dos logs..."
    
    # Logs do backend
    if [ -f "/home/ubuntu/azure-dashboard/azure-dashboard-backend/app.log" ]; then
        cp "/home/ubuntu/azure-dashboard/azure-dashboard-backend/app.log" \
           "$BACKUP_DIR/logs/backend_$DATE.log"
    fi
    
    # Logs do frontend
    if [ -f "/home/ubuntu/azure-dashboard/azure-dashboard-frontend/frontend.log" ]; then
        cp "/home/ubuntu/azure-dashboard/azure-dashboard-frontend/frontend.log" \
           "$BACKUP_DIR/logs/frontend_$DATE.log"
    fi
    
    log "✅ Backup dos logs concluído"
}

# Criar manifesto do backup
create_manifest() {
    log "Criando manifesto do backup..."
    
    cat > "$BACKUP_DIR/manifest_$DATE.json" << EOF
{
    "backup_date": "$DATE",
    "backup_type": "full",
    "files": {
        "database": "database/database_$DATE.db",
        "database_sql": "database/database_$DATE.sql",
        "config": "config/config_$DATE.tar.gz",
        "functions": "config/functions_$DATE.tar.gz",
        "logs": "logs/"
    },
    "system_info": {
        "hostname": "$(hostname)",
        "os": "$(uname -a)",
        "disk_usage": "$(df -h /home/ubuntu/azure-dashboard | tail -1)"
    }
}
EOF
    
    log "✅ Manifesto criado"
}

# Limpeza de backups antigos
cleanup_old_backups() {
    log "Limpando backups antigos (>$RETENTION_DAYS dias)..."
    
    find "$BACKUP_DIR" -name "*.db" -mtime +$RETENTION_DAYS -delete
    find "$BACKUP_DIR" -name "*.sql" -mtime +$RETENTION_DAYS -delete
    find "$BACKUP_DIR" -name "*.tar.gz" -mtime +$RETENTION_DAYS -delete
    find "$BACKUP_DIR" -name "*.log" -mtime +$RETENTION_DAYS -delete
    find "$BACKUP_DIR" -name "manifest_*.json" -mtime +$RETENTION_DAYS -delete
    
    log "✅ Limpeza concluída"
}

# Upload para Azure Storage (opcional)
upload_to_azure() {
    if [ ! -z "$AZURE_STORAGE_ACCOUNT" ] && [ ! -z "$AZURE_STORAGE_KEY" ]; then
        log "Fazendo upload para Azure Storage..."
        
        # Criar arquivo compactado com todo o backup
        tar -czf "/tmp/bolt_backup_$DATE.tar.gz" -C "$BACKUP_DIR" .
        
        # Upload usando Azure CLI
        az storage blob upload \
            --account-name "$AZURE_STORAGE_ACCOUNT" \
            --account-key "$AZURE_STORAGE_KEY" \
            --container-name "backups" \
            --name "bolt_backup_$DATE.tar.gz" \
            --file "/tmp/bolt_backup_$DATE.tar.gz"
        
        # Limpar arquivo temporário
        rm "/tmp/bolt_backup_$DATE.tar.gz"
        
        log "✅ Upload para Azure Storage concluído"
    else
        log "Variáveis do Azure Storage não configuradas, pulando upload"
    fi
}

# Função de restauração
restore_backup() {
    local backup_date=$1
    
    if [ -z "$backup_date" ]; then
        error "Data do backup não especificada. Use: ./backup.sh restore YYYYMMDD_HHMMSS"
    fi
    
    log "Restaurando backup de $backup_date..."
    
    # Parar serviços
    log "Parando serviços..."
    pkill -f "python3 src/main.py" || true
    pkill -f "npm run dev" || true
    
    # Restaurar banco de dados
    if [ -f "$BACKUP_DIR/database/database_$backup_date.db" ]; then
        log "Restaurando banco de dados..."
        cp "$BACKUP_DIR/database/database_$backup_date.db" "$DB_PATH"
        log "✅ Banco de dados restaurado"
    else
        error "Backup do banco de dados não encontrado para $backup_date"
    fi
    
    # Restaurar configurações
    if [ -f "$BACKUP_DIR/config/config_$backup_date.tar.gz" ]; then
        log "Restaurando configurações..."
        tar -xzf "$BACKUP_DIR/config/config_$backup_date.tar.gz" -C /
        log "✅ Configurações restauradas"
    else
        warn "Backup das configurações não encontrado para $backup_date"
    fi
    
    log "✅ Restauração concluída"
    log "Reinicie os serviços manualmente"
}

# Listar backups disponíveis
list_backups() {
    log "Backups disponíveis:"
    echo ""
    
    for manifest in "$BACKUP_DIR"/manifest_*.json; do
        if [ -f "$manifest" ]; then
            backup_date=$(basename "$manifest" | sed 's/manifest_\(.*\)\.json/\1/')
            backup_size=$(du -sh "$BACKUP_DIR" | cut -f1)
            echo "  📦 $backup_date (Tamanho: $backup_size)"
        fi
    done
    
    echo ""
}

# Verificar integridade dos backups
verify_backups() {
    log "Verificando integridade dos backups..."
    
    for db_backup in "$BACKUP_DIR"/database/database_*.db; do
        if [ -f "$db_backup" ]; then
            if sqlite3 "$db_backup" "PRAGMA integrity_check;" | grep -q "ok"; then
                log "✅ $(basename "$db_backup") - OK"
            else
                error "❌ $(basename "$db_backup") - CORROMPIDO"
            fi
        fi
    done
}

# Função principal
main() {
    case "${1:-backup}" in
        "backup")
            log "🔄 Iniciando backup completo..."
            create_backup_dir
            backup_database
            backup_config
            backup_logs
            create_manifest
            cleanup_old_backups
            upload_to_azure
            log "✅ Backup concluído: $DATE"
            ;;
        "restore")
            restore_backup "$2"
            ;;
        "list")
            list_backups
            ;;
        "verify")
            verify_backups
            ;;
        *)
            echo "Uso: $0 {backup|restore|list|verify}"
            echo ""
            echo "Comandos:"
            echo "  backup          - Fazer backup completo"
            echo "  restore DATE    - Restaurar backup específico"
            echo "  list           - Listar backups disponíveis"
            echo "  verify         - Verificar integridade dos backups"
            exit 1
            ;;
    esac
}

# Executar função principal
main "$@"

