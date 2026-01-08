#!/bin/bash

# Deployment Script
# Usage: ./deploy.sh [staging|production]

set -e  # Exit on error

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

ENV=${1:-staging}

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Deployment Script - ${ENV^^}${NC}"
echo -e "${BLUE}========================================${NC}\n"

# Step 1: Pre-deployment checks
echo -e "${YELLOW}Step 1: Pre-deployment checks${NC}"

# Check if git repo is clean
if [[ -n $(git status -s) ]]; then
    echo -e "${RED}Warning: Git working directory is not clean!${NC}"
    git status -s
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Check current branch
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
echo "Current branch: ${CURRENT_BRANCH}"

if [[ "${CURRENT_BRANCH}" != "main" ]] && [[ "${ENV}" == "production" ]]; then
    echo -e "${RED}Error: Production deployments must be from 'main' branch!${NC}"
    exit 1
fi

# Get current commit
COMMIT_HASH=$(git rev-parse --short HEAD)
echo "Commit: ${COMMIT_HASH}"

# Step 2: Backup database
echo -e "\n${YELLOW}Step 2: Backup database${NC}"
./backup_db.sh "${ENV}"

# Step 3: Run tests
echo -e "\n${YELLOW}Step 3: Running tests${NC}"
if command -v pytest &> /dev/null; then
    echo "Running unit tests..."
    pytest tests/test_*.py -v || {
        echo -e "${RED}Tests failed! Aborting deployment.${NC}"
        exit 1
    }
    echo -e "${GREEN}All tests passed!${NC}"
else
    echo -e "${YELLOW}pytest not found, skipping tests${NC}"
fi

# Step 4: Run migration
echo -e "\n${YELLOW}Step 4: Running database migration${NC}"

# Check current migration status
echo "Current migration status:"
alembic current

# Run migration
read -p "Run 'alembic upgrade head'? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    alembic upgrade head || {
        echo -e "${RED}Migration failed! Aborting deployment.${NC}"
        exit 1
    }
    echo -e "${GREEN}Migration completed!${NC}"

    # Verify migration
    echo "New migration status:"
    alembic current
else
    echo "Skipping migration..."
fi

# Step 5: Install dependencies
echo -e "\n${YELLOW}Step 5: Installing dependencies${NC}"
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt --quiet
    echo -e "${GREEN}Dependencies installed!${NC}"
fi

# Step 6: Restart service
echo -e "\n${YELLOW}Step 6: Restart service${NC}"
echo "Service restart command (manual):"
echo "  systemd: sudo systemctl restart backend-api"
echo "  docker: docker-compose restart backend"
echo "  manual: pkill -f uvicorn && uvicorn app.main:app &"

read -p "Restart service now? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Restarting service..."
    # Uncomment appropriate command:
    # sudo systemctl restart backend-api
    # docker-compose restart backend
    echo -e "${YELLOW}Please restart service manually${NC}"
fi

# Step 7: Health check
echo -e "\n${YELLOW}Step 7: Health check${NC}"
./health_check.sh

# Step 8: Summary
echo -e "\n${BLUE}========================================${NC}"
echo -e "${GREEN}Deployment Summary${NC}"
echo -e "${BLUE}========================================${NC}"
echo "Environment: ${ENV}"
echo "Commit: ${COMMIT_HASH}"
echo "Time: $(date)"
echo -e "\n${GREEN}Deployment completed successfully!${NC}"

# Post-deployment checklist
echo -e "\n${YELLOW}Post-deployment checklist:${NC}"
echo "[ ] Monitor logs for errors"
echo "[ ] Run smoke tests"
echo "[ ] Verify OAuth login works"
echo "[ ] Check admin endpoints"
echo "[ ] Monitor metrics for 1 hour"

exit 0
