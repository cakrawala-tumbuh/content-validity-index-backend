VENV_DIR := .venv
VENV_PYTHON := $(VENV_DIR)/bin/python
VENV_PIP := $(VENV_DIR)/bin/pip

.DEFAULT_GOAL := ci
.PHONY: install lint test ci clean

# Buat venv dan install dependensi (setara dengan setup di lint.yml)
$(VENV_DIR)/.installed: pyproject.toml
	python3 -m venv $(VENV_DIR)
	$(VENV_PIP) install --upgrade pip
	$(VENV_PIP) install ruff mypy
	$(VENV_PIP) install -e ".[dev]"
	touch $(VENV_DIR)/.installed

install: $(VENV_DIR)/.installed

# Sama dengan .github/workflows/lint.yml
lint: $(VENV_DIR)/.installed
	$(VENV_DIR)/bin/ruff check . && $(VENV_DIR)/bin/ruff format --check .
	$(VENV_DIR)/bin/mypy app/

# Sama dengan .github/workflows/test.yml
test:
	docker build -t cvi-backend:test .
	docker compose -f docker-compose.test.yml up \
		--build \
		--abort-on-container-exit \
		--exit-code-from test
	docker compose -f docker-compose.test.yml down --volumes

ci: lint test

clean:
	rm -rf $(VENV_DIR)
	docker compose -f docker-compose.test.yml down --volumes --rmi local 2>/dev/null || true
