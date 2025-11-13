.PHONY: help install test test-verbose test-cov test-watch lint format clean run dev docker-up docker-down docker-build

# Default target
help:
	@echo "Available commands:"
	@echo "  install      - Install dependencies"
	@echo "  test         - Run tests"
	@echo "  test-verbose - Run tests with verbose output"
	@echo "  test-cov     - Run tests with coverage report"
	@echo "  test-watch   - Run tests in watch mode"
	@echo "  lint         - Run code linting"
	@echo "  format       - Format code with black"
	@echo "  clean        - Clean up temporary files"
	@echo "  run          - Run the application"
	@echo "  dev          - Run in development mode"
	@echo "  docker-up    - Start Docker containers"
	@echo "  docker-down  - Stop Docker containers"
	@echo "  docker-build - Build Docker image"

# Installation
install:
	pip install -r requirements.txt
	pip install -e .

# Testing
test:
	pytest

test-verbose:
	pytest -v

test-cov:
	pytest --cov=app --cov=main --cov-report=term-missing --cov-report=html

test-watch:
	pytest --cov=app --cov=main -f

test-specific:
	pytest tests/$(TEST) -v

test-markers:
	pytest -m "$(MARKER)" -v

# Code quality
lint:
	flake8 app tests main.py
	mypy app tests main.py

format:
	black app tests main.py
	isort app tests main.py

# Cleanup
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf .coverage htmlcov/ .pytest_cache/ .mypy_cache/

# Running the application
run:
	uvicorn main:app --host 0.0.0.0 --port 8000

dev:
	uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# Docker commands
docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

docker-build:
	docker-compose build

docker-logs:
	docker-compose logs -f

docker-test:
	docker-compose run --rm backend pytest

docker-test-cov:
	docker-compose run --rm backend pytest --cov=app --cov=main --cov-report=term-missing

# Development helpers
setup-dev:
	pip install -r requirements.txt
	pip install pytest-flake8 pytest-black pytest-mypy black isort flake8 mypy pre-commit

pre-commit:
	pre-commit run --all-files

# Database
db-init:
	python -c "from main import init_db; init_db()"

# Documentation
docs:
	@echo "Generate API documentation:"
	@echo "Visit http://localhost:8000/docs when the application is running"

# Production
prod:
	uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4

prod-docker:
	docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Security
security-scan:
	bandit -r app main.py
	safety check