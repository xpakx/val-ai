.PHONY: run  eye

all: run

run:
	uv run --package agent python -m agent.main

eye:
	uv run --package eye python -m eye.example
