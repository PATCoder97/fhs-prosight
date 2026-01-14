# ============================================================================
# Makefile for FHS ProSight Docker Operations
# ============================================================================

.PHONY: help build up down restart logs clean prune test backend frontend

# Default target
help:
	@echo "FHS ProSight Docker Commands:"
	@echo ""
	@echo "  make build          - Build all Docker images"
	@echo "  make up             - Start all services"
	@echo "  make down           - Stop all services"
	@echo "  make restart        - Restart all services"
	@echo "  make logs           - View logs from all services"
	@echo "  make logs-backend   - View backend logs"
	@echo "  make logs-frontend  - View frontend logs"
	@echo "  make clean          - Stop and remove containers, networks"
	@echo "  make prune          - Clean up Docker system (WARNING: removes unused resources)"
	@echo "  make ps             - Show running containers"
	@echo "  make shell-backend  - Enter backend container shell"
	@echo "  make shell-frontend - Enter frontend container shell"
	@echo "  make build-backend  - Build only backend image"
	@echo "  make build-frontend - Build only frontend image"
	@echo "  make test           - Run backend tests"
	@echo ""

# Build all images
build:
	@echo "Building all Docker images..."
	docker-compose build

# Build backend only
build-backend:
	@echo "Building backend image..."
	docker-compose build backend

# Build frontend only
build-frontend:
	@echo "Building frontend image..."
	docker-compose build frontend

# Start all services
up:
	@echo "Starting all services..."
	docker-compose up -d

# Start with build
up-build:
	@echo "Building and starting all services..."
	docker-compose up -d --build

# Stop all services
down:
	@echo "Stopping all services..."
	docker-compose down

# Restart all services
restart:
	@echo "Restarting all services..."
	docker-compose restart

# Restart backend only
restart-backend:
	@echo "Restarting backend service..."
	docker-compose restart backend

# Restart frontend only
restart-frontend:
	@echo "Restarting frontend service..."
	docker-compose restart frontend

# View logs
logs:
	docker-compose logs -f

# View backend logs
logs-backend:
	docker-compose logs -f backend

# View frontend logs
logs-frontend:
	docker-compose logs -f frontend

# Show container status
ps:
	docker-compose ps

# Enter backend shell
shell-backend:
	docker-compose exec backend bash

# Enter frontend shell
shell-frontend:
	docker-compose exec frontend sh

# Clean up containers and networks
clean:
	@echo "Cleaning up containers and networks..."
	docker-compose down -v

# Prune Docker system
prune:
	@echo "WARNING: This will remove all unused containers, networks, images, and volumes!"
	@read -p "Are you sure? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		docker system prune -af --volumes; \
	fi

# Run tests in backend container
test:
	@echo "Running backend tests..."
	docker-compose exec backend pytest

# Health check
health:
	@echo "Checking service health..."
	@curl -f http://localhost:8000/health || echo "Backend: UNHEALTHY"
	@curl -f http://localhost:80/ || echo "Frontend: UNHEALTHY"

# Pull images from registry
pull:
	docker-compose pull

# Push images to registry (requires configuration)
push:
	@echo "Pushing images to registry..."
	docker-compose push

# Show resource usage
stats:
	docker stats

# Backup database (customize as needed)
backup-db:
	@echo "Creating database backup..."
	docker-compose exec backend pg_dump -U $(DB_USER) $(DB_NAME) > backup_$(shell date +%Y%m%d_%H%M%S).sql

# View environment variables
env:
	docker-compose config
