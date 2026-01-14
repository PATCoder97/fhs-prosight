#!/bin/bash

# ============================================================================
# Deploy Script với Subdomain Cookie Support
# ============================================================================
# Script này giúp deploy backend với COOKIE_DOMAIN configuration
# cho cross-subdomain authentication
# ============================================================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ============================================================================
# Helper Functions
# ============================================================================

print_header() {
    echo -e "${BLUE}================================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}================================================${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

# ============================================================================
# Configuration Detection
# ============================================================================

print_header "Subdomain Cookie Configuration Setup"

echo ""
echo "Bạn đang sử dụng kiến trúc nào?"
echo ""
echo "1) Single Domain (Khuyến nghị cho bảo mật)"
echo "   Frontend: https://tphomelab.io.vn"
echo "   Backend:  https://tphomelab.io.vn/api (nginx proxy)"
echo ""
echo "2) Separate Subdomains (Khuyến nghị cho scalability)"
echo "   Frontend: https://tphomelab.io.vn"
echo "   Backend:  https://api.tphomelab.io.vn"
echo ""
read -p "Chọn (1 hoặc 2): " architecture_choice

case $architecture_choice in
    1)
        print_info "Bạn chọn: Single Domain Architecture"
        USE_COOKIE_DOMAIN=false
        ;;
    2)
        print_info "Bạn chọn: Separate Subdomains Architecture"
        USE_COOKIE_DOMAIN=true
        ;;
    *)
        print_error "Lựa chọn không hợp lệ"
        exit 1
        ;;
esac

echo ""

# ============================================================================
# Collect Configuration
# ============================================================================

print_header "Thu thập thông tin cấu hình"

# Frontend URL
read -p "Frontend URL (e.g., https://tphomelab.io.vn): " FRONTEND_URL
if [[ -z "$FRONTEND_URL" ]]; then
    print_error "Frontend URL không được để trống"
    exit 1
fi

# Cookie Domain
if [[ "$USE_COOKIE_DOMAIN" == "true" ]]; then
    echo ""
    echo "Nhập root domain cho cookie sharing (PHẢI có dấu chấm ở đầu):"
    echo "Ví dụ: .tphomelab.io.vn (cho phép *.tphomelab.io.vn)"
    read -p "Cookie Domain: " COOKIE_DOMAIN

    # Validate leading dot
    if [[ ! "$COOKIE_DOMAIN" =~ ^\. ]]; then
        print_warning "Cookie domain nên bắt đầu bằng dấu chấm (.) để work với subdomain"
        read -p "Tự động thêm dấu chấm? (y/n): " add_dot
        if [[ "$add_dot" == "y" ]]; then
            COOKIE_DOMAIN=".$COOKIE_DOMAIN"
            print_success "Updated: $COOKIE_DOMAIN"
        fi
    fi
else
    COOKIE_DOMAIN=""
    print_info "Cookie Domain: (empty - same domain only)"
fi

# Cookie Secure
echo ""
if [[ "$FRONTEND_URL" =~ ^https:// ]]; then
    COOKIE_SECURE="true"
    print_success "Auto-detected HTTPS: COOKIE_SECURE=true"
else
    COOKIE_SECURE="false"
    print_warning "Auto-detected HTTP: COOKIE_SECURE=false (not recommended for production)"
fi

# ============================================================================
# Display Configuration Summary
# ============================================================================

print_header "Tóm tắt cấu hình"

echo ""
echo "FRONTEND_URL:    $FRONTEND_URL"
echo "COOKIE_DOMAIN:   ${COOKIE_DOMAIN:-'(empty)'}"
echo "COOKIE_SECURE:   $COOKIE_SECURE"
echo ""

read -p "Xác nhận cấu hình trên? (y/n): " confirm
if [[ "$confirm" != "y" ]]; then
    print_error "Đã hủy"
    exit 1
fi

# ============================================================================
# Pull Latest Images
# ============================================================================

print_header "Pulling latest Docker images"

print_info "Pulling backend image..."
docker pull patcoder97/prosight-backend:dev
print_success "Backend image pulled"

print_info "Pulling frontend image..."
docker pull patcoder97/prosight-frontend:dev
print_success "Frontend image pulled"

print_info "Pulling database image..."
docker pull postgres:16-alpine
print_success "Database image pulled"

# ============================================================================
# Create/Update Environment File
# ============================================================================

print_header "Creating environment configuration"

ENV_FILE=".env.deploy"

cat > "$ENV_FILE" << EOF
# ============================================================================
# Auto-generated Environment Configuration
# Generated: $(date)
# ============================================================================

# Frontend & Cookie Settings
FRONTEND_URL=$FRONTEND_URL
COOKIE_SECURE=$COOKIE_SECURE
COOKIE_DOMAIN=$COOKIE_DOMAIN

# ⚠️ IMPORTANT: Replace placeholders below with your actual credentials

# Database Configuration
POSTGRES_HOST=tp75-db
POSTGRES_PORT=5432
POSTGRES_USER=tp75user
POSTGRES_PASSWORD=tp75pass_change_in_production
POSTGRES_DATABASE=tp75db
DATABASE_URL=postgresql+asyncpg://tp75user:tp75pass_change_in_production@tp75-db:5432/tp75db

# OAuth - IMPORTANT: Replace with your own credentials
GOOGLE_CLIENT_ID=your_google_client_id_here
GOOGLE_CLIENT_SECRET=your_google_client_secret_here
GITHUB_CLIENT_ID=your_github_client_id_here
GITHUB_CLIENT_SECRET=your_github_client_secret_here

# JWT
SECRET_KEY=supersecrettuan123456_change_in_production
ACCESS_TOKEN_EXPIRE_MINUTES=1440
PRE_AUTH_TOKEN_EXPIRE_MINUTES=5
ALGORITHM=HS256

# PIDKey.com API - IMPORTANT: Replace with your own API key
PIDKEY_API_KEY=your_pidkey_api_key_here
PIDKEY_BASE_URL=https://pidkey.com/ajax/pidms_api

# FHS HRS Integration
FHS_HRS_BASE_URL=https://www.fhs.com.tw/ads/api/Furnace/rest/json/hr
EOF

print_success "Environment file created: $ENV_FILE"
print_warning "⚠️  Nhớ edit file $ENV_FILE để thay thế các placeholders bằng credentials thật!"

# ============================================================================
# Deploy with Docker Compose
# ============================================================================

print_header "Deploying services"

echo ""
read -p "Bạn muốn deploy ngay với docker-compose? (y/n): " deploy_now

if [[ "$deploy_now" == "y" ]]; then
    print_info "Starting deployment..."

    # Stop existing containers
    print_info "Stopping existing containers..."
    docker-compose -f docker-compose.prod.yml down || true

    # Deploy with new configuration
    print_info "Starting services with new configuration..."
    docker-compose --env-file "$ENV_FILE" -f docker-compose.prod.yml up -d

    print_success "Deployment completed!"

    echo ""
    print_header "Container Status"
    docker-compose -f docker-compose.prod.yml ps

    echo ""
    print_header "Logs"
    echo "Để xem logs, chạy:"
    echo "  docker-compose -f docker-compose.prod.yml logs -f"

else
    print_info "Deployment skipped"
    echo ""
    echo "Để deploy thủ công sau, chạy:"
    echo "  docker-compose --env-file $ENV_FILE -f docker-compose.prod.yml up -d"
fi

# ============================================================================
# Verification Steps
# ============================================================================

print_header "Next Steps - Verification"

echo ""
echo "1. Edit credentials trong file: $ENV_FILE"
echo "   - GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET"
echo "   - GITHUB_CLIENT_ID, GITHUB_CLIENT_SECRET"
echo "   - PIDKEY_API_KEY"
echo "   - SECRET_KEY"
echo "   - POSTGRES_PASSWORD"
echo ""
echo "2. Restart containers sau khi edit:"
echo "   docker-compose --env-file $ENV_FILE -f docker-compose.prod.yml up -d"
echo ""
echo "3. Verify cookie configuration:"
echo "   - Truy cập: $FRONTEND_URL"
echo "   - Login với Google/GitHub"
echo "   - Check DevTools → Application → Cookies"
echo "   - Cookie domain phải là: ${COOKIE_DOMAIN:-'(same as site)'}"
echo ""
echo "4. Test API calls:"
echo "   curl $FRONTEND_URL/api/health"
echo ""

if [[ "$USE_COOKIE_DOMAIN" == "true" ]]; then
    print_warning "⚠️  Subdomain Cookie Security Note:"
    echo "   Cookie với domain '$COOKIE_DOMAIN' sẽ accessible từ TẤT CẢ subdomain!"
    echo "   Đảm bảo không có subdomain không tin cậy trên domain này."
fi

echo ""
print_success "Setup completed! 🎉"
echo ""
echo "📖 Đọc thêm:"
echo "   - SUBDOMAIN_COOKIE_SETUP.md"
echo "   - OAUTH_CLOUDFLARE_FIX.md"
echo "   - DEPLOY_CASAOS.md"
echo ""
