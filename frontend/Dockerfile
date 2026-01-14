# ============================================================================
# Dockerfile cho FHS HR Integration Frontend
# Multi-stage build: Node Builder + Nginx Production
# ============================================================================

# Stage 1: Frontend Builder - Build Vue.js app
FROM node:18.20.8-alpine AS builder

WORKDIR /app

# Copy package files
COPY package*.json ./

# Cài đặt dependencies (ignore postinstall script vì source code chưa có)
RUN npm install --legacy-peer-deps --ignore-scripts

# Copy source code
COPY . .

# Chạy postinstall scripts sau khi đã có source code
RUN npm run build:icons && npm run msw:init

# Build production
RUN npm run build


# Stage 2: Production - Nginx server
FROM nginx:1.25-alpine

# Copy nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy built artifacts từ builder stage
COPY --from=builder /app/dist /usr/share/nginx/html

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD wget --quiet --tries=1 --spider http://localhost:5173/ || exit 1

# Expose port
EXPOSE 5173

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
