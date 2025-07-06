# Open Prices - Agent Development Guide

## Build/Test Commands
- **Run all tests**: `make django-tests`
- **Run single test**: `make django-tests-single args="test.module.TestClass.test_method"`
- **Lint code**: `make checks` (runs toml-check, flake8, black-check, mypy, isort-check, docs)
- **Format code**: `make black` and `make isort`
- **Type check**: `make mypy`
- **Database migrations**: `make makemigrations args="app_name"` and `make migrate-db`

## Code Style
- **Python version**: 3.11
- **Formatter**: Black (max line length 88)
- **Import sorting**: isort with black profile
- **Type checking**: mypy with strict mode enabled
- **Linting**: flake8 (ignores E203, E501, W503; max-line-length 88)

## Naming Conventions
- Models: PascalCase (e.g., `PriceQuerySet`)
- Functions/variables: snake_case (e.g., `has_discount()`)
- Constants: UPPER_SNAKE_CASE (e.g., `TYPE_PRODUCT`)
- Modules: snake_case with descriptive names

## Import Structure
1. Standard library imports
2. Third-party imports (Django, DRF, etc.)
3. Local application imports with full path (e.g., `from open_prices.common import constants`)

## Error Handling
- Use Django's ValidationError for model validation
- Type hints required for all functions and methods
- Prefer explicit typing over Any when possible

## Django Conventions
- Use Django's built-in authentication and session management
- Follow Django REST Framework patterns for API serializers
- Use factory-boy for test fixtures
- Leverage Django Q2 for async task processing