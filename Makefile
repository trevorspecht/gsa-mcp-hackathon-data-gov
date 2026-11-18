.PHONY: setup check security live build
setup:
	uv sync --locked
	uv run pre-commit install

check:
	uv run ruff check .
	uv run ruff format --check .
	uv run pytest -q
	uv run python scripts/check_docs.py
	$(MAKE) security
	$(MAKE) build

security:
	uv run bandit -q -r src
	uv run python scripts/check_secrets.py
	uv run pip-audit --progress-spinner off

build:
	uv build

live:
	uv run python scripts/live_smoke.py
