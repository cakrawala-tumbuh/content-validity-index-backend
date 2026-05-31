.PHONY: install lint test ci

install:
	pip install --upgrade pip
	pip install ruff mypy
	pip install -e ".[dev]"

# Sama dengan .github/workflows/lint.yml
lint:
	ruff check . && ruff format --check .
	mypy app/

# Sama dengan .github/workflows/test.yml
test:
	docker build -t cvi-backend:test .
	docker compose -f docker-compose.test.yml up \
		--abort-on-container-exit \
		--exit-code-from test
	docker compose -f docker-compose.test.yml down --volumes

ci: lint test
