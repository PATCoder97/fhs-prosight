#!/bin/bash

# Rollback Script
# Usage: ./rollback.sh [staging|production]

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

ENV=${1:-staging}

echo -e "${RED}========================================${NC}"
echo -e "${RED}ROLLBACK SCRIPT - ${ENV^^}${NC}"
echo -e "${RED}========================================${NC}\n"

echo -e "${YELLOW}This will rollback the last deployment!${NC}"
read -p "Are you sure you want to continue? (yes/no) " -r
echo
if [[ ! $REPLY == "yes" ]]; then
    echo "Rollback cancelled."
    exit 0
fi

# Step 1: Get previous commit
echo -e "${YELLOW}Step 1: Finding previous commit${NC}"

echo "Recent commits:"
git log --oneline -5

echo ""
read -p "Enter commit hash to rollback to: " ROLLBACK_COMMIT

if [ -z "$ROLLBACK_COMMIT" ]; then
    echo -e "${RED}Error: Commit hash required!${NC}"
    exit 1
fi

# Verify commit exists
if ! git cat-file -e "${ROLLBACK_COMMIT}^{commit}" 2>/dev/null; then
    echo -e "${RED}Error: Invalid commit hash!${NC}"
    exit 1
fi

echo -e "${GREEN}Rollback target: ${ROLLBACK_COMMIT}${NC}"

# Step 2: Backup current state
echo -e "\n${YELLOW}Step 2: Backup current database state${NC}"
./backup_db.sh "${ENV}"

# Step 3: Rollback code
echo -e "\n${YELLOW}Step 3: Rollback code to previous version${NC}"

git checkout "${ROLLBACK_COMMIT}"
echo -e "${GREEN}Code rolled back to ${ROLLBACK_COMMIT}${NC}"

# Step 4: Rollback migration
echo -e "\n${YELLOW}Step 4: Rollback database migration${NC}"

echo "Current migration status:"
alembic current

read -p "Rollback migration (alembic downgrade -1)? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    alembic downgrade -1 || {
        echo -e "${RED}Migration rollback failed!${NC}"
        echo "You may need to restore from backup"
        exit 1
    }
    echo -e "${GREEN}Migration rolled back!${NC}"

    echo "New migration status:"
    alembic current
fi

# Step 5: Reinstall dependencies
echo -e "\n${YELLOW}Step 5: Reinstall dependencies${NC}"
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt --quiet
    echo -e "${GREEN}Dependencies reinstalled!${NC}"
fi

# Step 6: Restart service
echo -e "\n${YELLOW}Step 6: Restart service${NC}"
echo "Service restart required:"
echo "  systemd: sudo systemctl restart backend-api"
echo "  docker: docker-compose restart backend"

read -p "Restart service now? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Restarting service..."
    # sudo systemctl restart backend-api
    echo -e "${YELLOW}Please restart service manually${NC}"
fi

# Step 7: Verify rollback
echo -e "\n${YELLOW}Step 7: Verify rollback${NC}"
./health_check.sh

# Summary
echo -e "\n${RED}========================================${NC}"
echo -e "${YELLOW}Rollback Summary${NC}"
echo -e "${RED}========================================${NC}"
echo "Environment: ${ENV}"
echo "Rolled back to: ${ROLLBACK_COMMIT}"
echo "Time: $(date)"

echo -e "\n${GREEN}Rollback completed!${NC}"

echo -e "\n${YELLOW}Post-rollback checklist:${NC}"
echo "[ ] Verify service is running"
echo "[ ] Run smoke tests"
echo "[ ] Check logs for errors"
echo "[ ] Verify OAuth login works"
echo "[ ] Monitor metrics"
echo "[ ] Notify team of rollback"
echo "[ ] Document rollback reason"

echo -e "\n${RED}WARNING: Remember to fix the issue before re-deploying!${NC}"

exit 0
