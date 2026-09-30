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

.PHONY: cohort features similarity similarity-evaluate phase2-build
cohort:
	uv run fri cohort build
features:
	uv run fri features build
similarity-evaluate:
	uv run fri similarity evaluate
similarity:
	uv run fri similarity build
phase2-build:
	uv run fri cohort build
	uv run fri features build
	uv run fri similarity evaluate
	uv run fri similarity build
	uv run python scripts/phase2_reports.py

.PHONY: translation-audit translation-data translation-validate translation-evaluate translation-publish phase3-build
translation-audit:
	uv run fri translation audit
translation-data:
	uv run fri translation data
	uv run python scripts/phase3_reports.py
translation-validate:
	uv run fri translation validate-models
translation-evaluate:
	uv run fri translation evaluate
translation-publish:
	uv run fri translation publish
phase3-build: translation-data translation-evaluate translation-publish
	uv run python scripts/translation_reports.py
	uv run python scripts/generate_contracts.py

.PHONY: phase4-build recruitment-evaluate
phase4-build:
	uv run fri recruitment build
	uv run python scripts/generate_contracts.py
recruitment-evaluate:
	uv run python scripts/recruitment_reproduce.py
