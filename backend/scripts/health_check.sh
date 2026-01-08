#!/bin/bash

# Health Check Script
# Usage: ./health_check.sh [API_URL]

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
API_URL=${1:-"http://localhost:8000"}
DB_HOST=${POSTGRES_HOST:-"ktxn258.duckdns.org"}
DB_PORT=${POSTGRES_PORT:-"6543"}
DB_USER=${POSTGRES_USER:-"casaos"}
DB_NAME=${POSTGRES_DB:-"casaos"}

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Health Check${NC}"
echo -e "${BLUE}========================================${NC}\n"

# Test results
TESTS_PASSED=0
TESTS_FAILED=0

# Helper function
check_test() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✓ PASS${NC}"
        ((TESTS_PASSED++))
    else
        echo -e "${RED}✗ FAIL${NC}"
        ((TESTS_FAILED++))
    fi
}

# Test 1: API Health Endpoint
echo -e "${YELLOW}Test 1: API Health Endpoint${NC}"
echo "URL: ${API_URL}/health"

if command -v curl &> /dev/null; then
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "${API_URL}/health" 2>/dev/null || echo "000")

    if [ "$HTTP_CODE" == "200" ]; then
        echo "Response: ${HTTP_CODE}"
        check_test 0
    else
        echo "Response: ${HTTP_CODE}"
        check_test 1
    fi
else
    echo -e "${YELLOW}curl not found, skipping HTTP test${NC}"
fi

# Test 2: Database Connection
echo -e "\n${YELLOW}Test 2: Database Connection${NC}"
echo "Host: ${DB_HOST}:${DB_PORT}"
echo "Database: ${DB_NAME}"

if command -v psql &> /dev/null; then
    if PGPASSWORD=${POSTGRES_PASSWORD} psql -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d "${DB_NAME}" -c "SELECT 1;" > /dev/null 2>&1; then
        echo "Connection: Success"
        check_test 0
    else
        echo "Connection: Failed"
        check_test 1
    fi
else
    echo -e "${YELLOW}psql not found, skipping database test${NC}"
fi

# Test 3: Migration Status
echo -e "\n${YELLOW}Test 3: Migration Status${NC}"

if command -v alembic &> /dev/null; then
    CURRENT_MIGRATION=$(alembic current 2>/dev/null | head -n 1)

    if [ -n "$CURRENT_MIGRATION" ]; then
        echo "Current: ${CURRENT_MIGRATION}"

        if echo "$CURRENT_MIGRATION" | grep -q "(head)"; then
            echo "Status: At head (latest migration)"
            check_test 0
        else
            echo -e "${YELLOW}Status: Not at head${NC}"
            check_test 1
        fi
    else
        echo "Status: Could not determine"
        check_test 1
    fi
else
    echo -e "${YELLOW}alembic not found, skipping migration test${NC}"
fi

# Test 4: Database Schema
echo -e "\n${YELLOW}Test 4: Database Schema (localId column)${NC}"

if command -v psql &> /dev/null; then
    COLUMN_EXISTS=$(PGPASSWORD=${POSTGRES_PASSWORD} psql -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d "${DB_NAME}" -t -c "SELECT column_name FROM information_schema.columns WHERE table_name='users' AND column_name='localId';" 2>/dev/null | xargs)

    if [ "$COLUMN_EXISTS" == "localId" ]; then
        echo "localId column: Exists"
        check_test 0
    else
        echo "localId column: Not found"
        check_test 1
    fi
fi

# Test 5: Sample Data Query
echo -e "\n${YELLOW}Test 5: Sample Data Query${NC}"

if command -v psql &> /dev/null; then
    USER_COUNT=$(PGPASSWORD=${POSTGRES_PASSWORD} psql -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d "${DB_NAME}" -t -c "SELECT COUNT(*) FROM users;" 2>/dev/null | xargs)

    if [ -n "$USER_COUNT" ] && [ "$USER_COUNT" -ge 0 ]; then
        echo "User count: ${USER_COUNT}"
        check_test 0
    else
        echo "User count: Query failed"
        check_test 1
    fi
fi

# Test 6: OAuth Endpoints (if URL provided)
if [[ "$API_URL" != "http://localhost:8000" ]]; then
    echo -e "\n${YELLOW}Test 6: OAuth Endpoints${NC}"

    if command -v curl &> /dev/null; then
        # Test Google OAuth endpoint
        GOOGLE_CODE=$(curl -s -o /dev/null -w "%{http_code}" "${API_URL}/api/auth/login/google" 2>/dev/null || echo "000")
        echo "Google OAuth: ${GOOGLE_CODE}"

        if [ "$GOOGLE_CODE" == "307" ] || [ "$GOOGLE_CODE" == "302" ] || [ "$GOOGLE_CODE" == "200" ]; then
            check_test 0
        else
            check_test 1
        fi

        # Test GitHub OAuth endpoint
        GITHUB_CODE=$(curl -s -o /dev/null -w "%{http_code}" "${API_URL}/api/auth/login/github" 2>/dev/null || echo "000")
        echo "GitHub OAuth: ${GITHUB_CODE}"

        if [ "$GITHUB_CODE" == "307" ] || [ "$GITHUB_CODE" == "302" ] || [ "$GITHUB_CODE" == "200" ]; then
            check_test 0
        else
            check_test 1
        fi
    fi
fi

# Summary
echo -e "\n${BLUE}========================================${NC}"
echo -e "${BLUE}Health Check Summary${NC}"
echo -e "${BLUE}========================================${NC}"

TOTAL_TESTS=$((TESTS_PASSED + TESTS_FAILED))
echo "Tests run: ${TOTAL_TESTS}"
echo -e "Passed: ${GREEN}${TESTS_PASSED}${NC}"
echo -e "Failed: ${RED}${TESTS_FAILED}${NC}"

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "\n${GREEN}All health checks passed!${NC}"
    exit 0
else
    echo -e "\n${RED}Some health checks failed!${NC}"
    exit 1
fi
