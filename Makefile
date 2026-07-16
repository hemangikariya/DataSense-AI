.PHONY: build up down logs restart migrate test lint format clean help

help:
	@echo "DataSense AI - Development Makefile"
	@echo "Available commands:"
	@echo "  build        - Build Docker containers"
	@echo "  up           - Start Docker containers"
	@echo "  down         - Stop Docker containers and clean volumes"
	@echo "  logs         - Tail logs from all containers"
	@echo "  restart      - Restart all services"
	@echo "  migrate      - Run Alembic database migrations"
	@echo "  test         - Run backend tests inside local venv"
	@echo "  lint         - Check Python code quality with Ruff"
	@echo "  format       - Format Python code with Ruff"
	@echo "  clean        - Remove temporary cache files"

build:
	docker-compose build

up:
	docker-compose up -d

down:
	docker-compose down -v

logs:
	docker-compose logs -f

restart:
	docker-compose restart

migrate:
	docker-compose exec backend alembic upgrade head

test:
	cd backend && pytest

lint:
	cd backend && ruff check .

format:
	cd backend && ruff format .

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -exec rm -rf {} +
	find . -type d -name ".next" -exec rm -rf {} +
	find . -type d -name "node_modules" -exec rm -rf {} +
