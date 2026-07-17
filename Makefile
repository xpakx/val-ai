.PHONY: run  eye test lint check

all: run

run:
	uv run --package agent python -m agent.main

eye:
	uv run --package eye python -m eye.example

test:
	uvx run pytest

lint:
	uvx ruff format

check:
	uvx ruff check
