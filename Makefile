PYTHON ?= python3

.PHONY: download analysis test report paper clean

download:
	$(PYTHON) scripts/download_data.py

analysis:
	$(PYTHON) src/analysis.py --input data/raw/colombianos_detenidos.csv

test:
	$(PYTHON) -m unittest discover -s tests -v

report:
	cd reports && pandoc informe_actualizado_2026.md \
		-o Informe_actualizado_2026.pdf \
		--pdf-engine=pdflatex \
		-V fontsize=11pt \
		-V geometry:margin=2.5cm \
		-V fontenc=T1 \
		--resource-path=.:../outputs/figures

paper:
	cd reports && pdflatex -interaction=nonstopmode -halt-on-error paper_2026.tex
	cd reports && bibtex paper_2026
	cd reports && pdflatex -interaction=nonstopmode -halt-on-error paper_2026.tex
	cd reports && pdflatex -interaction=nonstopmode -halt-on-error paper_2026.tex

clean:
	rm -rf data/processed/* outputs/tables/* outputs/figures/* outputs/models/*
