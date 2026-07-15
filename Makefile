.PHONY: run 

all: run

run:
	uv run --package agent python -m agent.main
