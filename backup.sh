#!/bin/bash

# WhatsApp Chat Viewer - Backup and Monitoring Script
# Usage: ./backup.sh [backup|restore|monitor]

COMMAND=${1:-backup}
BACKUP_DIR="./backups"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

case $COMMAND in
    backup)
        echo "🗄️ Creating backup..."
        mkdir -p $BACKUP_DIR
        
        # Backup database
        docker-compose exec postgres pg_dump -U ${POSTGRES_USER:-postgres} whatsapp_chat > $BACKUP_DIR/db_backup_$TIMESTAMP.sql
        
        # Backup uploads
        tar -czf $BACKUP_DIR/uploads_backup_$TIMESTAMP.tar.gz uploads/
        
        echo "✅ Backup created: $BACKUP_DIR/db_backup_$TIMESTAMP.sql"
        echo "✅ Uploads backed up: $BACKUP_DIR/uploads_backup_$TIMESTAMP.tar.gz"
        ;;
        
    restore)
        BACKUP_FILE=${2:-$(ls -t $BACKUP_DIR/db_backup_*.sql | head -1)}
        echo "🔄 Restoring from: $BACKUP_FILE"
        docker-compose exec -T postgres psql -U ${POSTGRES_USER:-postgres} whatsapp_chat < $BACKUP_FILE
        echo "✅ Database restored"
        ;;
        
    monitor)
        echo "📊 System Status:"
        echo "=================="
        docker-compose ps
        echo ""
        echo "💾 Disk Usage:"
        df -h
        echo ""
        echo "🐳 Docker Stats:"
        docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}"
        ;;
        
    *)
        echo "Usage: $0 [backup|restore|monitor]"
        exit 1
        ;;
esac