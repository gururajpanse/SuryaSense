.PHONY: setup lint test manifest nowcast train eval app clean

setup:
	pip install -e ".[dev]"

lint:
	ruff check src/ tests/ scripts/
	mypy src/

test:
	pytest

manifest:
	python scripts/make_manifest.py

nowcast:
	python -m solarflare.nowcast.pipeline

train:
	python -m solarflare.forecast.train

eval:
	python -m solarflare.forecast.evaluate

app:
	streamlit run app/main.py

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -exec rm -rf {} +
