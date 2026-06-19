# Makefile
# Common commands for Docker and development

.PHONY: help build up down logs shell test clean

help:
	@echo "Available commands:"
	@echo "  make build    - Build Docker images"
	@echo "  make up       - Start services"
	@echo "  make down     - Stop services"
	@echo "  make logs     - View logs"
	@echo "  make shell    - Open shell in backend container"
	@echo "  make test     - Run tests"
	@echo "  make clean    - Clean up containers and volumes"

build:
	docker-compose build

up:
	docker-compose up -d

up-dev:
	docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d

down:
	docker-compose down

down-clean:
	docker-compose down -v

logs:
	docker-compose logs -f

logs-backend:
	docker-compose logs -f backend

shell:
	docker-compose exec backend /bin/bash

test:
	docker-compose exec backend pytest -v

test-cov:
	docker-compose exec backend pytest --cov=app --cov-report=term-missing

migrate:
	docker-compose exec backend alembic upgrade head

migrate-create:
	docker-compose exec backend alembic revision --autogenerate -m "$(message)"

clean:
	docker-compose down -v
	docker system prune -f

restart:
	docker-compose restart

status:
	docker-compose ps

# Production commands
prod-build:
	docker-compose -f docker-compose.yml -f docker-compose.prod.yml build

prod-up:
	docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

prod-down:
	docker-compose -f docker-compose.yml -f docker-compose.prod.yml down

# Database commands
db-backup:
	docker-compose exec postgres pg_dump -U $(POSTGRES_USER) $(POSTGRES_DB) > backup_$(shell date +%Y%m%d_%H%M%S).sql

db-restore:
	docker-compose exec -T postgres psql -U $(POSTGRES_USER) $(POSTGRES_DB) < $(file)