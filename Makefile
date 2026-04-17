.PHONY: install test lint lint-fix run clean

install:
	uv sync --extra dev

test:
	uv run pytest tests/ -v --cov=search_keyword_revenue --cov-fail-under=90

lint:
	uv run ruff check src/ tests/

lint-fix:
	uv run ruff check --fix src/ tests/

format:
	uv run ruff format src/ tests/

run:
	uv run python -m search_keyword_revenue.cli data/sample_input.tsv

clean:
	find . -type d -name __pycache__ | xargs rm -rf
	find . -type d -name .mypy_cache | xargs rm -rf
	find . -type d -name .ruff_cache | xargs rm -rf
	find . -type d -name .pytest_cache | xargs rm -rf
	find . -type d -name "*.egg-info" | xargs rm -rf
	find . -name "*.pyc" -delete
	find . -name coverage.xml -delete
	find . -name .coverage -delete
