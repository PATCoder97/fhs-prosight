#!/bin/bash

# ============================================================================
# Script kiểm tra môi trường Docker trước khi build
# ============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "=========================================="
echo "FHS ProSight - Docker Environment Check"
echo "=========================================="
echo ""

# Function to print status
print_status() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✓${NC} $2"
    else
        echo -e "${RED}✗${NC} $2"
        FAILED=1
    fi
}

FAILED=0

# Check Docker
echo "Checking Docker installation..."
if command -v docker &> /dev/null; then
    DOCKER_VERSION=$(docker --version)
    print_status 0 "Docker installed: $DOCKER_VERSION"
else
    print_status 1 "Docker is not installed"
fi

# Check Docker Compose
echo ""
echo "Checking Docker Compose..."
if command -v docker-compose &> /dev/null; then
    COMPOSE_VERSION=$(docker-compose --version)
    print_status 0 "Docker Compose installed: $COMPOSE_VERSION"
else
    print_status 1 "Docker Compose is not installed"
fi

# Check if Docker daemon is running
echo ""
echo "Checking Docker daemon..."
if docker info &> /dev/null; then
    print_status 0 "Docker daemon is running"
else
    print_status 1 "Docker daemon is not running"
fi

# Check .env file
echo ""
echo "Checking configuration files..."
if [ -f ".env" ]; then
    print_status 0 ".env file exists"

    # Check required variables
    required_vars=("DATABASE_URL" "DB_HOST" "DB_NAME" "DB_USER" "DB_PASSWORD" "FIREBASE_API_KEY" "SECRET_KEY")

    for var in "${required_vars[@]}"; do
        if grep -q "^$var=" .env; then
            value=$(grep "^$var=" .env | cut -d '=' -f2)
            if [ -n "$value" ] && [[ ! "$value" =~ ^your- ]] && [[ ! "$value" =~ ^replace- ]]; then
                print_status 0 "  $var is configured"
            else
                print_status 1 "  $var needs to be configured (currently has placeholder value)"
            fi
        else
            print_status 1 "  $var is missing"
        fi
    done
else
    print_status 1 ".env file not found (copy from .env.example)"
fi

# Check firebase_credentials.json
echo ""
if [ -f "backend/firebase_credentials.json" ]; then
    print_status 0 "firebase_credentials.json exists"
else
    print_status 1 "backend/firebase_credentials.json not found"
fi

# Check Dockerfile
echo ""
echo "Checking Dockerfiles..."
if [ -f "backend/Dockerfile" ]; then
    print_status 0 "backend/Dockerfile exists"
else
    print_status 1 "backend/Dockerfile not found"
fi

if [ -f "frontend/Dockerfile" ]; then
    print_status 0 "frontend/Dockerfile exists"
else
    print_status 1 "frontend/Dockerfile not found"
fi

# Check docker-compose.yml
echo ""
if [ -f "docker-compose.yml" ]; then
    print_status 0 "docker-compose.yml exists"
else
    print_status 1 "docker-compose.yml not found"
fi

# Check disk space
echo ""
echo "Checking system resources..."
AVAILABLE_SPACE=$(df -h . | awk 'NR==2 {print $4}')
echo -e "${GREEN}✓${NC} Available disk space: $AVAILABLE_SPACE"

# Summary
echo ""
echo "=========================================="
if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}All checks passed!${NC}"
    echo "You can now run: docker-compose up -d --build"
else
    echo -e "${RED}Some checks failed!${NC}"
    echo "Please fix the issues above before building Docker images."
    exit 1
fi
echo "=========================================="
