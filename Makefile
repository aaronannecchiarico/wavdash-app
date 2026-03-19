.PHONY: help dev dev-local stop build clean test lint format \
        app-shell audio-shell marketing-shell logs install

# Default target
.DEFAULT_GOAL := help

# Colors for output
CYAN := \033[0;36m
GREEN := \033[0;32m
YELLOW := \033[0;33m
RED := \033[0;31m
RESET := \033[0m

##@ General

help: ## Display this help message
	@awk 'BEGIN {FS = ":.*##"; printf "\n$(CYAN)Usage:$(RESET)\n  make $(GREEN)<target>$(RESET)\n"} /^[a-zA-Z_-]+:.*?##/ { printf "  $(CYAN)%-20s$(RESET) %s\n", $$1, $$2 } /^##@/ { printf "\n$(YELLOW)%s$(RESET)\n", substr($$0, 5) } ' $(MAKEFILE_LIST)
	@echo ""
	@echo "$(YELLOW)Container Runtime:$(RESET) Colima (brew install colima docker docker-compose)"
	@echo "$(YELLOW)Local Database:$(RESET) SQLite (no setup needed)"
	@echo "$(YELLOW)Docker Database:$(RESET) MySQL 8.0 (managed by docker-compose)"

colima-start: ## Start Colima container runtime
	@echo "$(GREEN)Starting Colima...$(RESET)"
	@colima start --cpu 4 --memory 8

colima-stop: ## Stop Colima container runtime
	@echo "$(YELLOW)Stopping Colima...$(RESET)"
	@colima stop

colima-status: ## Check Colima status
	@colima status

##@ Development (Docker via Colima)

dev: ## Start all services in development mode with Docker
	@echo "$(CYAN)Checking Colima status...$(RESET)"
	@colima status > /dev/null 2>&1 || (echo "$(RED)Colima is not running. Start it with: colima start$(RESET)" && exit 1)
	@echo "$(GREEN)Starting WavDash monorepo in development mode...$(RESET)"
	docker-compose -f docker-compose.yml -f docker-compose.dev.yml up

dev-detached: ## Start all services in development mode (detached)
	@echo "$(CYAN)Checking Colima status...$(RESET)"
	@colima status > /dev/null 2>&1 || (echo "$(RED)Colima is not running. Start it with: colima start$(RESET)" && exit 1)
	@echo "$(GREEN)Starting WavDash monorepo in development mode (detached)...$(RESET)"
	docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d
	@echo "$(GREEN)Services started! (Using MySQL in Docker)$(RESET)"
	@echo "App: http://localhost:8000"
	@echo "Audio Service: http://localhost:8001"
	@echo "Marketing: http://localhost:4321"
	@echo "Flower (Celery): http://localhost:5555"
	@echo "phpMyAdmin: http://localhost:8080"
	@echo "Redis Commander: http://localhost:8081"
	@echo "MailHog: http://localhost:8025"

stop: ## Stop all Docker services
	@echo "$(YELLOW)Stopping all services...$(RESET)"
	docker-compose -f docker-compose.yml -f docker-compose.dev.yml down

build: ## Build all Docker images
	@echo "$(GREEN)Building all Docker images...$(RESET)"
	docker-compose -f docker-compose.yml -f docker-compose.dev.yml build

clean: ## Remove all Docker containers, volumes, and images
	@echo "$(RED)Cleaning up Docker resources...$(RESET)"
	docker-compose -f docker-compose.yml -f docker-compose.dev.yml down -v --rmi all

##@ Development (Local - No Docker)

dev-local: ## Start all services locally (no Docker)
	@echo "$(GREEN)Starting local development...$(RESET)"
	@echo "$(YELLOW)Uses SQLite for Laravel database (no MySQL needed)$(RESET)"
	@echo "$(YELLOW)You need to run these in separate terminals:$(RESET)"
	@echo ""
	@echo "Terminal 1 - Laravel App (SQLite):"
	@echo "  cd app && composer run dev"
	cd app && composer run dev
	@echo ""
	@echo "Terminal 2 - Audio Service Worker:"
	@echo "  cd audio-service && source wavdash-audio-extraction-service-local/bin/activate && python scripts/start_worker.py"
	@echo ""
	@echo "Terminal 3 - Audio Service API:"
	@echo "  cd audio-service && source wavdash-audio-extraction-service-local/bin/activate && uvicorn main:app --reload --port 8001"
	@echo ""
	@echo "Terminal 4 - Marketing Site:"
	@echo "  cd marketing && npm run dev"
	@echo ""
	@echo "$(CYAN)Note: Redis is optional for local dev (use QUEUE_CONNECTION=sync)$(RESET)"

install: ## Install dependencies for all services
	@echo "$(GREEN)Installing dependencies for all services...$(RESET)"
	@echo "$(CYAN)Installing Laravel dependencies...$(RESET)"
	cd app && composer install && npm install
	@echo "$(CYAN)Installing Audio Service dependencies...$(RESET)"
	cd audio-service && python3 -m venv venv && source venv/bin/activate && python3 scripts/install.py
	@echo "$(CYAN)Installing Marketing dependencies...$(RESET)"
	cd marketing && npm install
	@echo "$(GREEN)All dependencies installed!$(RESET)"

##@ Testing

test: ## Run all test suites
	@echo "$(GREEN)Running all tests...$(RESET)"
	@$(MAKE) test-app
	@$(MAKE) test-audio
	@$(MAKE) test-marketing

test-app: ## Run Laravel tests
	@echo "$(CYAN)Running Laravel tests...$(RESET)"
	cd app && composer run test

test-audio: ## Run audio service tests
	@echo "$(CYAN)Running audio service tests...$(RESET)"
	cd audio-service && ./scripts/run_tests.sh

test-marketing: ## Build marketing site (test)
	@echo "$(CYAN)Building marketing site...$(RESET)"
	cd marketing && npm run build

##@ Code Quality

lint: ## Run linters for all services
	@echo "$(GREEN)Running linters...$(RESET)"
	cd app && npm run lint
	cd audio-service && ./scripts/format_code.sh
	cd marketing && npm run build

format: ## Format code for all services
	@echo "$(GREEN)Formatting code...$(RESET)"
	cd app && vendor/bin/pint
	cd audio-service && ./scripts/format_code.sh

analyse: ## Run static analysis
	@echo "$(GREEN)Running static analysis...$(RESET)"
	cd app && composer run analyse

##@ Database

migrate: ## Run Laravel migrations
	@echo "$(GREEN)Running migrations...$(RESET)"
	cd app && php artisan migrate

migrate-fresh: ## Fresh migration with seeding
	@echo "$(YELLOW)Running fresh migration...$(RESET)"
	cd app && php artisan migrate:fresh-with-microservice --seed

##@ Docker Utilities

app-shell: ## Open shell in Laravel container
	docker-compose -f docker-compose.yml -f docker-compose.dev.yml exec app sh

audio-shell: ## Open shell in audio service container
	docker-compose -f docker-compose.yml -f docker-compose.dev.yml exec audio-api sh

marketing-shell: ## Open shell in marketing container
	docker-compose -f docker-compose.yml -f docker-compose.dev.yml exec marketing sh

logs: ## View logs for all services
	docker-compose -f docker-compose.yml -f docker-compose.dev.yml logs -f

logs-app: ## View Laravel logs
	docker-compose -f docker-compose.yml -f docker-compose.dev.yml logs -f app

logs-audio: ## View audio service logs
	docker-compose -f docker-compose.yml -f docker-compose.dev.yml logs -f audio-api audio-worker

logs-marketing: ## View marketing site logs
	docker-compose -f docker-compose.yml -f docker-compose.dev.yml logs -f marketing

##@ Production

prod: ## Start services in production mode
	@echo "$(GREEN)Starting WavDash in production mode...$(RESET)"
	docker-compose up -d
	@echo "$(GREEN)Production services started!$(RESET)"

prod-stop: ## Stop production services
	@echo "$(YELLOW)Stopping production services...$(RESET)"
	docker-compose down

##@ Pi Development

PI_HOST ?= aannecchiarico@raspberrypi.local
PI_DIR ?= /home/aannecchiarico/wavdash
PI_VENV ?= /home/aannecchiarico/venv

pi-sync: ## Sync pi/ folder to Raspberry Pi
	@echo "$(GREEN)Syncing pi/ to $(PI_HOST):$(PI_DIR)...$(RESET)"
	rsync -avz --delete --exclude='__pycache__' --exclude='.pytest_cache' --exclude='*.pyc' \
		pi/ $(PI_HOST):$(PI_DIR)/
	@echo "$(GREEN)Sync complete!$(RESET)"

pi-ssh: ## Open SSH session to Raspberry Pi
	ssh $(PI_HOST)

pi-test: pi-sync ## Sync code then run tests on Pi
	@echo "$(GREEN)Running tests on Pi...$(RESET)"
	ssh $(PI_HOST) "cd $(PI_DIR) && source $(PI_VENV)/bin/activate && python -m pytest -v"

pi-run: pi-sync ## Sync code then run the player on Pi
	@echo "$(GREEN)Starting player on Pi...$(RESET)"
	ssh $(PI_HOST) "cd $(PI_DIR) && source $(PI_VENV)/bin/activate && python main.py"

pi-receiver: pi-sync ## Sync code then start the receiver service on Pi
	@echo "$(GREEN)Starting receiver on Pi...$(RESET)"
	ssh $(PI_HOST) "cd $(PI_DIR) && source $(PI_VENV)/bin/activate && cd receiver && uvicorn main:app --host 0.0.0.0 --port 9000"
