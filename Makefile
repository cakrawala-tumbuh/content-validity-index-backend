IMAGE_NAME ?= $(shell basename $(CURDIR))-test
DOCKER_RUN  = docker run --rm $(IMAGE_NAME)

.DEFAULT_GOAL := test
.PHONY: build lint unit test clean help

build: ## Bangun image test (deps + tooling + source)
	docker build -f Dockerfile.test -t $(IMAGE_NAME) .

lint: build ## Jalankan linter (Ruff + mypy) di dalam container
	$(DOCKER_RUN) sh -c "ruff check . && ruff format --check . && mypy app/"

unit: build ## Jalankan unit test (pytest) di dalam container
	docker run --rm \
		-e DATABASE_URL="sqlite+aiosqlite:///:memory:" \
		-e AUTHENTIK_ISSUER_URL="https://authentik.test/application/o/cvi/" \
		-e AUTHENTIK_ADMIN_GROUP="cvi-admin" \
		-e AUTHENTIK_EXPERT_GROUP="cvi-expert" \
		-e APP_ENV="testing" \
		-e 'CORS_ORIGINS=["http://localhost:3000"]' \
		$(IMAGE_NAME) python -m pytest tests/ -v

test: lint unit ## Gate lengkap = lint + unit (dipakai lokal & CI)

clean: ## Hapus image test
	-docker rmi $(IMAGE_NAME)

help: ## Tampilkan daftar target
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-8s\033[0m %s\n", $$1, $$2}'
