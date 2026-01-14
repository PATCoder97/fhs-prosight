#!/bin/bash

# ============================================================================
# Script deploy nhanh cho FHS ProSight
# ============================================================================

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "=========================================="
echo "FHS ProSight - Quick Deploy Script"
echo "=========================================="
echo ""

# Check if .env exists
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}Warning: .env file not found. Copying from .env.example...${NC}"
    cp .env.example .env
    echo "Please edit .env file with your actual configuration before continuing."
    exit 1
fi

# Pull latest code
echo -e "${GREEN}Step 1:${NC} Pulling latest code from Git..."
git pull origin main

# Stop existing containers
echo ""
echo -e "${GREEN}Step 2:${NC} Stopping existing containers..."
docker-compose down

# Build images
echo ""
echo -e "${GREEN}Step 3:${NC} Building Docker images..."
docker-compose build --no-cache

# Start services
echo ""
echo -e "${GREEN}Step 4:${NC} Starting services..."
docker-compose up -d

# Wait for services to be healthy
echo ""
echo -e "${GREEN}Step 5:${NC} Waiting for services to be healthy..."
sleep 10

# Check health
echo ""
echo -e "${GREEN}Step 6:${NC} Checking service health..."

BACKEND_HEALTH=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health || echo "000")
FRONTEND_HEALTH=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:80/ || echo "000")

if [ "$BACKEND_HEALTH" = "200" ]; then
    echo -e "${GREEN}✓${NC} Backend is healthy (HTTP $BACKEND_HEALTH)"
else
    echo -e "${YELLOW}⚠${NC} Backend returned HTTP $BACKEND_HEALTH"
fi

if [ "$FRONTEND_HEALTH" = "200" ]; then
    echo -e "${GREEN}✓${NC} Frontend is healthy (HTTP $FRONTEND_HEALTH)"
else
    echo -e "${YELLOW}⚠${NC} Frontend returned HTTP $FRONTEND_HEALTH"
fi

# Show running containers
echo ""
echo -e "${GREEN}Step 7:${NC} Running containers:"
docker-compose ps

# Summary
echo ""
echo "=========================================="
echo -e "${GREEN}Deployment complete!${NC}"
echo ""
echo "Access points:"
echo "  - Frontend: http://localhost:80"
echo "  - Backend API: http://localhost:8000"
echo "  - API Docs: http://localhost:8000/docs"
echo ""
echo "Useful commands:"
echo "  - View logs: docker-compose logs -f"
echo "  - Stop services: docker-compose down"
echo "  - Restart: docker-compose restart"
echo "=========================================="
