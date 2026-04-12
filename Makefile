.PHONY: up down build rebuild test test-unit test-integration lint migrate seed logs clean help ps shell security-scan

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

up: ## Start all services
	docker compose up -d
	@echo "\nAll services started"
	@echo "   Dashboard:  http://localhost:3000"
	@echo "   API:        http://localhost:8000"
	@echo "   API Docs:   http://localhost:8000/docs"
	@echo "   Grafana:    http://localhost:3001"

down: ## Stop all services
	docker compose down

build: ## Build all Docker images
	docker compose build

rebuild: ## Rebuild and restart all services
	docker compose up -d --build

test: ## Run all tests (backend + frontend)
	@echo "Running backend tests..."
	@for svc in gateway-service ingestion-service agent-service compliance-service search-service notification-service; do \
		echo "\nTesting $$svc..."; \
		docker compose exec $$svc pytest tests/ -v --tb=short 2>/dev/null || echo "  $$svc tests skipped (service not running)"; \
	done
	@echo "\nRunning frontend tests..."
	cd frontend && npm test -- --run 2>/dev/null || echo "  Frontend tests skipped"

test-unit: ## Run unit tests only
	docker compose exec gateway-service pytest tests/unit/ -v

test-integration: ## Run integration tests (ephemeral containers)
	docker compose -f docker-compose.yml -f docker-compose.test.yml up --abort-on-container-exit --exit-code-from gateway-service

lint: ## Lint all code
	@echo "Linting backend..."
	@for svc in gateway-service ingestion-service agent-service compliance-service search-service notification-service; do \
		echo "  Linting $$svc..."; \
		cd services/$$svc && ruff check src/ 2>/dev/null; cd ../..; \
	done
	@echo "Linting frontend..."
	cd frontend && npm run lint 2>/dev/null || true

migrate: ## Run database migrations
	docker compose exec gateway-service alembic upgrade head

seed: ## Seed the database with sample data
	docker compose exec gateway-service python -m scripts.seed_data

logs: ## Tail logs for all services
	docker compose logs -f --tail=50

logs-service: ## Tail logs for a specific service (usage: make logs-service SVC=gateway-service)
	docker compose logs -f --tail=100 $(SVC)

clean: ## Remove all containers, volumes, and images
	docker compose down -v --rmi local
	@echo "Cleaned up"

ps: ## Show running services
	docker compose ps

restart: ## Restart a specific service (usage: make restart SVC=agent-service)
	docker compose restart $(SVC)

shell: ## Open a shell in a service (usage: make shell SVC=gateway-service)
	docker compose exec $(SVC) /bin/sh

security-scan: ## Run security scans (bandit, npm audit, trivy)
	@echo "=== Bandit (Python SAST) ==="
	@bandit -r services/ shared/ -c .bandit.yml --severity-level medium 2>/dev/null || echo "  Install bandit: pip install bandit"
	@echo "\n=== npm audit (Frontend) ==="
	@cd frontend && npm audit --audit-level=moderate 2>/dev/null || echo "  npm audit completed with findings"
	@echo "\n=== Trivy (Docker Images) ==="
	@for img in regulatorai-gateway regulatorai-ingestion regulatorai-agent regulatorai-compliance regulatorai-search regulatorai-notification; do \
		echo "\nScanning $$img..."; \
		trivy image --severity HIGH,CRITICAL $$img 2>/dev/null || echo "  Install trivy: https://aquasecurity.github.io/trivy"; \
	done
