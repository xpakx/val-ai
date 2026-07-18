.PHONY: check test

check:
	uvx pyrefly check
	uvx ruff check
	uvx ruff format --diff

test:
	uv run --dev pytest

format:
	uvx ruff format
	uvx ruff check --fix
