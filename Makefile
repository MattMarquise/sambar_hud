.PHONY: help install dev run docker-build docker-run docker-stop clean test setup-pi

help: ## Show this help message
	@echo "Sambar HUD - Development Commands"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install Python dependencies locally
	pip3 install -r requirements.txt

dev: ## Set up development environment on Mac
	./dev_setup_mac.sh

run: ## Run the application (on Pi; or with DISPLAY=:99 for headless)
	python3 main.py

docker-build: ## Build Docker image for development
	docker-compose build

docker-run: ## Run application in Docker container
	docker-compose up

docker-stop: ## Stop Docker container
	docker-compose down

clean: ## Clean up generated files
	find . -type d -name __pycache__ -exec rm -r {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name ".xvfb.pid" -delete
	rm -rf build/ dist/ *.egg-info

test: ## Run tests (placeholder)
	@echo "Tests not yet implemented"

setup-pi: ## Setup instructions for Raspberry Pi
	@echo "To set up on Raspberry Pi:"
	@echo "1. Copy this directory to your Raspberry Pi"
	@echo "2. Run: ./setup_kiosk.sh"
	@echo "3. Reboot: sudo reboot"

start-vfb: ## Start virtual framebuffer for local testing
	./start_virtual_display.sh

stop-vfb: ## Stop virtual framebuffer
	./stop_virtual_display.sh
