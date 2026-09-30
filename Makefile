.PHONY: setup test lint typecheck data-bootstrap data-statsbomb data-tracking data-build data-validate data-coverage contracts dev api build smoke
setup:
	uv sync --frozen
	cd apps/web && npm ci
lint:
	uv run ruff check src tests scripts
	uv run ruff format --check src tests scripts
	cd apps/web && npm run lint
typecheck:
	uv run mypy src
	cd apps/web && npm run typecheck
test: lint typecheck
	uv run pytest -q
	uv run python scripts/generate_contracts.py --check
	cd apps/web && npm test
data-bootstrap:
	uv run fri data bootstrap
data-statsbomb:
	uv run fri data fetch statsbomb
data-tracking:
	uv run fri data fetch skillcorner
data-build:
	uv run fri data build
data-validate:
	uv run fri data validate
data-coverage:
	uv run fri data coverage
contracts:
	uv run python scripts/generate_contracts.py
dev:
	cd apps/web && npm run dev
api:
	uv run uvicorn football_intelligence.api:app --reload --host 127.0.0.1 --port 8000
build:
	cd apps/web && npm run build
smoke:
	cd apps/web && npm run test:smoke
