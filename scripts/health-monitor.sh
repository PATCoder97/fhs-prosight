#!/bin/bash

# ============================================================================
# Script giám sát health check cho FHS ProSight
# ============================================================================

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Function to check service health
check_health() {
    SERVICE_NAME=$1
    URL=$2

    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$URL" 2>/dev/null || echo "000")

    if [ "$HTTP_CODE" = "200" ]; then
        echo -e "${GREEN}✓${NC} $SERVICE_NAME is healthy (HTTP $HTTP_CODE)"
        return 0
    else
        echo -e "${RED}✗${NC} $SERVICE_NAME is unhealthy (HTTP $HTTP_CODE)"
        return 1
    fi
}

# Function to check container status
check_container() {
    CONTAINER_NAME=$1

    STATUS=$(docker inspect -f '{{.State.Status}}' "$CONTAINER_NAME" 2>/dev/null || echo "not found")

    if [ "$STATUS" = "running" ]; then
        echo -e "${GREEN}✓${NC} Container $CONTAINER_NAME is running"
        return 0
    else
        echo -e "${RED}✗${NC} Container $CONTAINER_NAME is $STATUS"
        return 1
    fi
}

# Main monitoring loop
INTERVAL=${1:-30}  # Default 30 seconds
FAILURES=0
MAX_FAILURES=3

echo "=========================================="
echo "FHS ProSight - Health Monitor"
echo "=========================================="
echo "Monitoring interval: ${INTERVAL}s"
echo "Press Ctrl+C to stop"
echo "=========================================="
echo ""

while true; do
    TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[$TIMESTAMP] Checking services..."

    CURRENT_FAILURES=0

    # Check containers
    check_container "fhs-backend" || ((CURRENT_FAILURES++))
    check_container "fhs-frontend" || ((CURRENT_FAILURES++))

    # Check HTTP endpoints
    check_health "Backend API" "http://localhost:8000/health" || ((CURRENT_FAILURES++))
    check_health "Frontend" "http://localhost:80/" || ((CURRENT_FAILURES++))

    # Check Docker stats
    echo ""
    echo "Resource usage:"
    docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}" fhs-backend fhs-frontend 2>/dev/null || echo "Unable to get stats"

    echo ""

    # Alert if failures detected
    if [ $CURRENT_FAILURES -gt 0 ]; then
        ((FAILURES++))
        echo -e "${YELLOW}⚠ Detected $CURRENT_FAILURES issue(s). Total failures: $FAILURES${NC}"

        if [ $FAILURES -ge $MAX_FAILURES ]; then
            echo -e "${RED}✗ Maximum failures reached ($MAX_FAILURES). Service may be down!${NC}"
            echo "Check logs with: docker-compose logs -f"
        fi
    else
        FAILURES=0
        echo -e "${GREEN}All services are healthy${NC}"
    fi

    echo "=========================================="
    sleep $INTERVAL
done
