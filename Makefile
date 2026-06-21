.PHONY: install api web test lint format typecheck evaluate docker-up docker-down

install:
	python -m pip install --upgrade pip
	pip install -e ".[dev]"

api:
	uvicorn signalscope.api.main:app --reload --host 0.0.0.0 --port 8000

web:
	cd apps/web && npm install && npm run dev

test:
	pytest

lint:
	ruff check src tests scripts

format:
	ruff format src tests scripts

typecheck:
	mypy src

evaluate:
	python scripts/run_evaluations.py

docker-up:
	docker compose up --build

docker-down:
	docker compose down --remove-orphans
