# Payment Tracker - Local Development Makefile
# Automates virtual environment setup and testing

# Variables
VENV_DIR = venv
PYTHON = python3
PIP = $(VENV_DIR)/bin/pip
PYTHON_VENV = $(VENV_DIR)/bin/python
REQUIREMENTS = requirements.txt
TEST_SCRIPT = test_local.py

# Colors for output
GREEN = \033[0;32m
YELLOW = \033[0;33m
RED = \033[0;31m
NC = \033[0m # No Color

# Default target
.PHONY: help
help:
	@echo "$(GREEN)Payment Tracker - Local Development$(NC)"
	@echo ""
	@echo "Available commands:"
	@echo "  $(YELLOW)make setup$(NC)       - Create virtual environment and install dependencies"
	@echo "  $(YELLOW)make test$(NC)        - Run configuration test only"
	@echo "  $(YELLOW)make metrics$(NC)     - Test metrics functionality"
	@echo "  $(YELLOW)make run$(NC)         - Run full payment extraction"
	@echo "  $(YELLOW)make test-verbose$(NC) - Run test with verbose logging"
	@echo "  $(YELLOW)make run-verbose$(NC)  - Run extraction with verbose logging"
	@echo "  $(YELLOW)make check-env$(NC)    - Check if virtual environment is active"
	@echo "  $(YELLOW)make clean$(NC)       - Remove virtual environment"
	@echo "  $(YELLOW)make status$(NC)      - Show environment status"
	@echo ""
	@echo "Quick start:"
	@echo "  1. $(YELLOW)make setup$(NC)     - Set up environment"
	@echo "  2. $(YELLOW)make test$(NC)      - Test configuration"
	@echo "  3. $(YELLOW)make run$(NC)       - Run extraction"

# Check if virtual environment exists
.PHONY: check-venv
check-venv:
	@if [ ! -d "$(VENV_DIR)" ]; then \
		echo "$(RED)Virtual environment not found. Run 'make setup' first.$(NC)"; \
		exit 1; \
	fi

# Check if virtual environment is active
.PHONY: check-env
check-env:
	@if [ -z "$$VIRTUAL_ENV" ]; then \
		echo "$(YELLOW)Virtual environment not active$(NC)"; \
		echo "To activate manually: $(GREEN)source $(VENV_DIR)/bin/activate$(NC)"; \
		echo "Or use make commands which auto-activate"; \
	else \
		echo "$(GREEN)Virtual environment active: $$VIRTUAL_ENV$(NC)"; \
	fi

# Create virtual environment and install dependencies
.PHONY: setup
setup:
	@echo "$(GREEN)Setting up local development environment...$(NC)"
	@if [ ! -d "$(VENV_DIR)" ]; then \
		echo "$(YELLOW)Creating virtual environment...$(NC)"; \
		$(PYTHON) -m venv $(VENV_DIR); \
	else \
		echo "$(YELLOW)Virtual environment already exists$(NC)"; \
	fi
	@echo "$(YELLOW)Installing dependencies...$(NC)"
	@$(PIP) install --upgrade pip
	@$(PIP) install -r $(REQUIREMENTS)
	@echo "$(GREEN)Setup complete!$(NC)"
	@echo ""
	@echo "Next steps:"
	@echo "1. Add your service account JSON to: $(YELLOW)credentials/service_account.json$(NC)"
	@echo "2. Set environment variables in $(YELLOW).env$(NC)"
	@echo "3. Run: $(YELLOW)make test$(NC)"

# Check if credentials file exists
.PHONY: check-credentials
check-credentials:
	@if [ ! -f "credentials/service_account.json" ]; then \
		echo "$(RED)Error: Service account file not found$(NC)"; \
		echo "Please add your Google Cloud service account JSON to:"; \
		echo "  $(YELLOW)credentials/service_account.json$(NC)"; \
		exit 1; \
	fi

# Check if .env file has required variables
.PHONY: check-env-vars
check-env-vars:
	@if [ ! -f ".env" ]; then \
		echo "$(RED)Error: .env file not found$(NC)"; \
		echo "Please create .env file with required variables"; \
		exit 1; \
	fi
	@if ! grep -q "GMAIL_APP_PASSWORD=" .env || grep -q "GMAIL_APP_PASSWORD=your_gmail_app_password" .env; then \
		echo "$(RED)Error: GMAIL_APP_PASSWORD not set in .env$(NC)"; \
		exit 1; \
	fi
	@if ! grep -q "GOOGLE_SPREADSHEET_ID=" .env || grep -q "GOOGLE_SPREADSHEET_ID=your_google_spreadsheet_id" .env; then \
		echo "$(RED)Error: GOOGLE_SPREADSHEET_ID not set in .env$(NC)"; \
		exit 1; \
	fi

# Pre-flight checks
.PHONY: preflight
preflight: check-venv check-credentials check-env-vars
	@echo "$(GREEN)Pre-flight checks passed$(NC)"

# Test configuration only
.PHONY: test
test: preflight
	@echo "$(GREEN)Running configuration test...$(NC)"
	@set -a; source .env; set +a; $(PYTHON_VENV) $(TEST_SCRIPT) --test

# Test metrics functionality
.PHONY: metrics
metrics: preflight
	@echo "$(GREEN)Testing metrics functionality...$(NC)"
	@set -a; source .env; set +a; $(PYTHON_VENV) $(TEST_SCRIPT) --metrics

# Run full payment extraction
.PHONY: run
run: preflight
	@echo "$(GREEN)Running payment extraction...$(NC)"
	@set -a; source .env; set +a; $(PYTHON_VENV) $(TEST_SCRIPT)

# Test with verbose logging
.PHONY: test-verbose
test-verbose: preflight
	@echo "$(GREEN)Running configuration test (verbose)...$(NC)"
	@set -a; source .env; set +a; $(PYTHON_VENV) $(TEST_SCRIPT) --test --verbose

# Run with verbose logging
.PHONY: run-verbose
run-verbose: preflight
	@echo "$(GREEN)Running payment extraction (verbose)...$(NC)"
	@set -a; source .env; set +a; $(PYTHON_VENV) $(TEST_SCRIPT) --verbose

# Show environment status
.PHONY: status
status:
	@echo "$(GREEN)Environment Status$(NC)"
	@echo "=================="
	@echo "Virtual environment: $(if $(wildcard $(VENV_DIR)),$(GREEN)EXISTS$(NC),$(RED)NOT FOUND$(NC))"
	@echo "Service account:     $(if $(wildcard credentials/service_account.json),$(GREEN)EXISTS$(NC),$(RED)NOT FOUND$(NC))"
	@echo "Environment file:    $(if $(wildcard .env),$(GREEN)EXISTS$(NC),$(RED)NOT FOUND$(NC))"
	@if [ -f ".env" ]; then \
		echo "Gmail password:      $(if $(shell grep -q 'GMAIL_APP_PASSWORD=.*[^r]$$' .env && echo 1),$(GREEN)SET$(NC),$(RED)NOT SET$(NC))"; \
		echo "Spreadsheet ID:      $(if $(shell grep -q 'GOOGLE_SPREADSHEET_ID=.*[^e]$$' .env && echo 1),$(GREEN)SET$(NC),$(RED)NOT SET$(NC))"; \
	fi
	@$(MAKE) check-env

# Clean up virtual environment
.PHONY: clean
clean:
	@echo "$(YELLOW)Removing virtual environment...$(NC)"
	@rm -rf $(VENV_DIR)
	@echo "$(GREEN)Clean complete$(NC)"

# Reinstall dependencies
.PHONY: reinstall
reinstall: clean setup

# Quick development cycle
.PHONY: dev
dev: setup test

# Production-like test (full run)
.PHONY: prod-test
prod-test: setup run

# Show Python and pip versions
.PHONY: versions
versions: check-venv
	@echo "$(GREEN)Versions$(NC)"
	@echo "========"
	@echo "System Python: $(shell $(PYTHON) --version)"
	@echo "Venv Python:   $(shell $(PYTHON_VENV) --version)"
	@echo "Pip:           $(shell $(PIP) --version)"

# Install additional package (usage: make install PACKAGE=package_name)
.PHONY: install
install: check-venv
	@if [ -z "$(PACKAGE)" ]; then \
		echo "$(RED)Usage: make install PACKAGE=package_name$(NC)"; \
		exit 1; \
	fi
	@echo "$(YELLOW)Installing $(PACKAGE)...$(NC)"
	@$(PIP) install $(PACKAGE)

# Update requirements.txt with current packages
.PHONY: freeze
freeze: check-venv
	@echo "$(YELLOW)Updating requirements.txt...$(NC)"
	@$(PIP) freeze > requirements-dev.txt
	@echo "$(GREEN)Dependencies saved to requirements-dev.txt$(NC)"