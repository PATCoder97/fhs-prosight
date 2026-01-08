#!/bin/bash

# Database Backup Script
# Usage: ./backup_db.sh [staging|production]

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
ENV=${1:-staging}
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="../backups"
BACKUP_FILE="${ENV}_backup_${TIMESTAMP}.sql"

# Database credentials (from .env or environment variables)
DB_HOST=${POSTGRES_HOST:-"ktxn258.duckdns.org"}
DB_PORT=${POSTGRES_PORT:-"6543"}
DB_USER=${POSTGRES_USER:-"casaos"}
DB_NAME=${POSTGRES_DB:-"casaos"}

echo -e "${YELLOW}Starting database backup for ${ENV}...${NC}"
echo "Host: ${DB_HOST}:${DB_PORT}"
echo "Database: ${DB_NAME}"
echo "Backup file: ${BACKUP_FILE}"

# Create backup directory if it doesn't exist
mkdir -p "${BACKUP_DIR}"

# Run pg_dump
echo -e "${YELLOW}Running pg_dump...${NC}"

if PGPASSWORD=${POSTGRES_PASSWORD} pg_dump \
    -h "${DB_HOST}" \
    -p "${DB_PORT}" \
    -U "${DB_USER}" \
    -d "${DB_NAME}" \
    -F p \
    --no-owner \
    --no-acl \
    > "${BACKUP_DIR}/${BACKUP_FILE}"; then

    echo -e "${GREEN}Backup completed successfully!${NC}"

    # Verify backup file
    BACKUP_SIZE=$(du -h "${BACKUP_DIR}/${BACKUP_FILE}" | cut -f1)
    echo "Backup size: ${BACKUP_SIZE}"

    # List recent backups
    echo -e "\n${GREEN}Recent backups:${NC}"
    ls -lht "${BACKUP_DIR}"/${ENV}_backup_* | head -5

    # Compress backup (optional)
    if command -v gzip &> /dev/null; then
        echo -e "${YELLOW}Compressing backup...${NC}"
        gzip "${BACKUP_DIR}/${BACKUP_FILE}"
        echo -e "${GREEN}Compressed to: ${BACKUP_FILE}.gz${NC}"
    fi

    echo -e "\n${GREEN}Backup location: ${BACKUP_DIR}/${BACKUP_FILE}${NC}"

else
    echo -e "${RED}Backup failed!${NC}"
    exit 1
fi

# Cleanup old backups (keep last 5)
echo -e "${YELLOW}Cleaning up old backups (keeping last 5)...${NC}"
ls -t "${BACKUP_DIR}"/${ENV}_backup_* 2>/dev/null | tail -n +6 | xargs -r rm
echo -e "${GREEN}Cleanup completed.${NC}"

echo -e "\n${GREEN}Backup process completed successfully!${NC}"
