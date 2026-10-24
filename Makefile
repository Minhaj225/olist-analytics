PYTHON ?= python

.PHONY: up down ingest build check analyze export test all
up:
	docker compose up -d --wait
	$(PYTHON) -m src.db
down:
	docker compose down
ingest:
	$(PYTHON) -m src.ingest
build:
	$(PYTHON) -m src.run_sql
check:
	$(PYTHON) -m src.quality_checks
analyze:
	$(PYTHON) -m src.analysis.kpis
	$(PYTHON) -m src.analysis.hypothesis_tests
	$(PYTHON) -m src.analysis.rfm
	$(PYTHON) -m src.analysis.forecast
export:
	$(PYTHON) -m src.export_extracts
test:
	$(PYTHON) -m pytest -q
all: up ingest build check analyze export test
