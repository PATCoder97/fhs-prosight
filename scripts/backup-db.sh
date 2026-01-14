#!/bin/bash

# ============================================================================
# Script backup database cho FHS ProSight
# ============================================================================

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Load environment variables
if [ -f ".env" ]; then
    export $(cat .env | grep -v '^#' | xargs)
else
    echo -e "${RED}Error: .env file not found${NC}"
    exit 1
fi

# Create backup directory
BACKUP_DIR="backups"
mkdir -p "$BACKUP_DIR"

# Generate backup filename with timestamp
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/fhs_prosight_backup_$TIMESTAMP.sql"

echo "=========================================="
echo "FHS ProSight - Database Backup"
echo "=========================================="
echo ""
echo -e "${GREEN}Database:${NC} $DB_NAME"
echo -e "${GREEN}Host:${NC} $DB_HOST"
echo -e "${GREEN}Backup file:${NC} $BACKUP_FILE"
echo ""

# Create backup
echo "Creating backup..."
PGPASSWORD=$DB_PASSWORD pg_dump \
    -h $DB_HOST \
    -p $DB_PORT \
    -U $DB_USER \
    -d $DB_NAME \
    -F p \
    --clean \
    --create \
    --if-exists \
    > "$BACKUP_FILE"

# Compress backup
echo "Compressing backup..."
gzip "$BACKUP_FILE"
BACKUP_FILE="$BACKUP_FILE.gz"

# Get file size
FILE_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)

echo ""
echo -e "${GREEN}✓ Backup completed successfully!${NC}"
echo -e "  File: $BACKUP_FILE"
echo -e "  Size: $FILE_SIZE"
echo ""

# Keep only last 7 backups
echo "Cleaning old backups (keeping last 7)..."
cd "$BACKUP_DIR"
ls -t fhs_prosight_backup_*.sql.gz | tail -n +8 | xargs -r rm --
cd ..

echo -e "${GREEN}✓ Cleanup completed${NC}"
echo "=========================================="
