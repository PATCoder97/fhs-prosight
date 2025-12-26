# ============================================================================
# Multi-stage Dockerfile cho FHS HR Integration Backend + Frontend
# Stage 1: Frontend Builder - Build Vue.js app
# Stage 2: Python Builder - Cài đặt Python dependencies
# Stage 3: Production - Image cuối cùng
# ============================================================================

# Stage 1: Frontend Builder - Build Vue.js
FROM node:18.20.8-alpine AS frontend-builder

WORKDIR /frontend

# Copy frontend
COPY frontend/ .

# Cài đặt dependencies và build
RUN npm install --legacy-peer-deps && npm run build


# Stage 2: Python Builder - Cài đặt Python dependencies
FROM python:3.11-slim AS python-builder

WORKDIR /tmp

# Biến môi trường
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Cài đặt pip và dependencies
RUN pip install --upgrade pip setuptools wheel

# Copy requirements và cài đặt
COPY backend/requirements.txt .
RUN pip install -r requirements.txt


# Stage 3: Production Runtime
FROM python:3.11-slim

WORKDIR /app

# Biến môi trường
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/app:$PATH"

# Cài đặt curl cho health check
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

# Copy Python dependencies từ python-builder
COPY --from=python-builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=python-builder /usr/local/bin /usr/local/bin

# Copy backend application code
COPY backend/ .

# Copy frontend built artifacts vào static folder (same level as app)
COPY --from=frontend-builder /frontend/dist ./static

# Copy start script
COPY backend/start.sh /app/start.sh
RUN chmod +x /app/start.sh

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose port
EXPOSE 8000

# Run start script
ENTRYPOINT ["/app/start.sh"]
