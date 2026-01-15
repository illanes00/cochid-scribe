.PHONY: dev dev-frontend dev-backend setup install test lint clean

# Development (runs frontend and backend in parallel)
dev:
	$(MAKE) -j2 dev-frontend dev-backend

dev-frontend:
	cd frontend && npm run dev

dev-backend:
	cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Setup
setup: install db-init
	cp -n .env.example .env || true
	@echo ""
	@echo "Setup complete!"
	@echo "Edit .env with your ANTHROPIC_API_KEY if you want LLM features."
	@echo ""
	@echo "Run 'make dev' to start development servers."

install:
	cd frontend && npm install
	cd backend && pip install -r requirements.txt

install-dev:
	cd frontend && npm install
	cd backend && pip install -r requirements-dev.txt

# Database (SQLite for local dev)
db-init:
	cd backend && python -c "from app.db.session import init_db; init_db()"
	@echo "Database initialized."

db-reset:
	rm -f backend/scribe.db
	$(MAKE) db-init
	@echo "Database reset complete."

# Testing
test: test-frontend test-backend

test-frontend:
	cd frontend && npm test

test-backend:
	cd backend && pytest

# Linting
lint: lint-frontend lint-backend

lint-frontend:
	cd frontend && npm run lint

lint-backend:
	cd backend && ruff check . && ruff format --check .

format:
	cd frontend && npm run format
	cd backend && ruff format .

# Clean
clean:
	cd frontend && rm -rf .next node_modules
	cd backend && rm -rf __pycache__ .pytest_cache .ruff_cache scribe.db
	@echo "Cleaned build artifacts."

# Help
help:
	@echo "Scribe Development Commands:"
	@echo ""
	@echo "  make setup        - Initial project setup (install deps + init DB)"
	@echo "  make dev          - Start development servers (frontend + backend)"
	@echo "  make test         - Run all tests"
	@echo "  make lint         - Run linters"
	@echo "  make format       - Format code"
	@echo "  make db-reset     - Reset local database"
	@echo "  make clean        - Clean build artifacts"
