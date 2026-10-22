PYTHON ?= python3
VENV ?= .venv
PY ?= $(VENV)/bin/python
PIP ?= $(VENV)/bin/pip
UVICORN ?= $(PY) -m uvicorn
API_PORT ?= 8000

.PHONY: install install-web download warehouse validate refresh analysis test test-api test-web test-e2e api web build-web report paper clean help

help:
	@echo "Targets:"
	@echo "  install        Create .venv and install Python dependencies"
	@echo "  install-web    Install the Next.js frontend dependencies"
	@echo "  download       Download the latest raw CSV"
	@echo "  warehouse      Build data/processed/detentions.parquet + manifest"
	@echo "  validate       Validate warehouse + manifest invariants"
	@echo "  refresh        download + warehouse + validate"
	@echo "  analysis       Regenerate tables, figures and model metrics"
	@echo "  test           Run all Python tests"
	@echo "  api            Run FastAPI on port $(API_PORT)"
	@echo "  web            Run Next.js on port 3000"
	@echo "  build-web      Production build of the frontend"
	@echo "  report         Build the working report PDF"
	@echo "  paper          Build the LaTeX paper"
	@echo "  clean          Remove generated data and outputs"

install:
	$(PYTHON) -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements-dev.txt

install-web:
	cd apps/web && pnpm install

download:
	$(PY) scripts/download_data.py

warehouse:
	$(PY) pipeline/build_warehouse.py

validate:
	$(PY) pipeline/validate_warehouse.py

refresh: download warehouse validate

analysis:
	$(PY) src/analysis.py --input data/raw/colombianos_detenidos.csv

test:
	$(PY) -m pytest tests pipeline/tests apps/api/tests -q

test-api:
	$(PY) -m pytest apps/api/tests -q

test-web:
	cd apps/web && pnpm typecheck

test-e2e:
	cd apps/web && pnpm test:e2e

api:
	$(UVICORN) apps.api.app.main:app --reload --port $(API_PORT)

web:
	cd apps/web && pnpm dev

build-web:
	cd apps/web && pnpm build

report:
	cd reports && pandoc informe_actualizado_2026.md \
		-o Informe_actualizado_2026.pdf \
		--pdf-engine=pdflatex \
		-V fontsize=11pt \
		-V geometry:margin=2.5cm \
		-V fontenc=T1 \
		--resource-path=.:../outputs/figures

paper:
	cd paper && pdflatex -interaction=nonstopmode -halt-on-error paper_2026.tex
	cd paper && bibtex paper_2026
	cd paper && pdflatex -interaction=nonstopmode -halt-on-error paper_2026.tex
	cd paper && pdflatex -interaction=nonstopmode -halt-on-error paper_2026.tex

clean:
	rm -rf data/processed/* outputs/tables/* outputs/figures/* outputs/models/*
