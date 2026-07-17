# AI Agent Instructions for Open Prices Backend

Welcome to the `open-prices` backend repository! As an AI coding assistant, please follow these guidelines when reading, writing, or refactoring code in this project.

## 1. Project Context
- **Purpose**: The Django backend and API for Open Prices (part of the Open Food Facts ecosystem).
- **API Docs**: https://prices.openfoodfacts.org/api/docs
- **Frontend**: Serves the [open-prices-frontend](https://github.com/openfoodfacts/open-prices-frontend).
- **Core Features**: Stores product prices, manages users, and asynchronously runs Machine Learning models (Triton, Gemini, Google Cloud Vision) for OCR and price tag detection.

## 2. Tech Stack & Architecture
- **Language**: Python 3.11+
- **Framework**: Django 5.2 + Django REST Framework (DRF)
- **Database**: PostgreSQL (via `psycopg2`)
- **Package Manager**: [uv](https://github.com/astral-sh/uv)
- **Task Queue**: Django Q2 (for async ML jobs)
- **Linting & Formatting**: Ruff, mypy
- **Testing**: Django's native test runner (`manage.py test`) / pytest

## 3. Strict Boundary Rules ("Never Touch")
Do **NOT** modify the following files or directories:
- **`uv.lock`**: Never hand-edit this file. **DO NOT use `pip install`**. Always use `uv add` or `uv sync` to manage dependencies.
- **CI/CD Configs**: Do not modify files in `.github/workflows/` or `.pre-commit-config.yaml` without explicit user permission.
- **Generated Docs**: Do not manually edit files inside `docs/schema/` or other auto-generated directories unless instructed.

## 4. Code & Architecture Conventions

### Code Examples Over Prose
When adding new endpoints, use DRF generic views or ViewSets and keep business logic out of the views. Use Type Hints (enforced by mypy).

**Example: A basic DRF ViewSet with Type Hints**
```python
from rest_framework import viewsets
from django.db.models import QuerySet
from .models import Price
from .serializers import PriceSerializer

class PriceViewSet(viewsets.ModelViewSet):
    queryset: QuerySet[Price] = Price.objects.all()
    serializer_class = PriceSerializer
    
    def perform_create(self, serializer: PriceSerializer) -> None:
        # Save logic here
        serializer.save(user=self.request.user)
```

### Directory Structure
- `/config/`: The Django project configuration (settings, WSGI, ASGI, root URL conf). **Do NOT add settings or URL patterns to `/open_prices/`** — they belong here.
- `/open_prices/`: Django apps organized by domain (e.g., `prices/`, `products/`, `proofs/`, `locations/`). Each app contains `models.py`, `views.py`, `serializers.py`, and `tests.py`.
- `/open_prices/api/`: DRF API layer with per-app sub-directories for views, serializers, and tests.
- `/scripts/`: Helper scripts for data imports, anonymization, etc.

### Migrations
- **Do NOT auto-generate migrations** without explicit user permission. If your model changes require a migration, note it and let the developer run `make makemigrations` themselves.

## 5. Testing Guidance
- **Location**: Tests live inside each Django app as `tests.py` (e.g., `open_prices/prices/tests.py`, `open_prices/api/prices/tests.py`). Add new tests in the relevant app's `tests.py`.
- **When to add tests**: Add a new test when introducing a new API endpoint, adding a complex model method, or fixing a bug.
- **Command**: Run tests locally using `uv run --env-file .env python manage.py test`

## 6. Commit & PR Conventions
- **Commit Messages**: Follow [Conventional Commits](https://www.conventionalcommits.org/). **CRITICAL**: This repo uses `release-please` for automated versioning. Your commit prefix directly drives the release pipeline and version bumps!
  - `feat: [description]` for new features (triggers Minor release).
  - `fix: [description]` for bug fixes (triggers Patch release).
  - `chore: [description]` for dependency updates or routine tasks.
  - `docs: [description]` for documentation changes (does **not** trigger a version bump).
- **Linting**: The project uses `pre-commit` hooks (Ruff only). Ensure your code passes Ruff formatting (`uv run ruff check . --fix && uv run ruff format .`). mypy is **not** part of pre-commit and must be run separately: `uv run mypy .`.

## 7. Common Commands (uv / Make)

> **Note**: Most commands require `--env-file .env` or the Makefile (which auto-loads `.env`). Never forget the env file when running Django management commands directly.

- **Install/Sync**: `uv sync`
- **Run Server**: `uv run --env-file .env python manage.py runserver`
- **Linting**: `uv run pre-commit run --all-files`
- **Tests**: `uv run --env-file .env python manage.py test` (or `make django-tests` via Docker)
- **Migrations**: `make makemigrations` / `make migrate-db`
- **Run CLI tasks**: `make cli args='<management_command>'` (e.g., `make cli args='run_ml_models'`)
- **Docker**: `make up` (start all), `make down` (stop all), `make log` (tail logs)
