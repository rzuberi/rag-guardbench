PYTHON ?= .venv/bin/python

.PHONY: run generate-data test

run:
	$(PYTHON) -m rag_guardbench.cli run --output-dir artifacts

generate-data:
	$(PYTHON) -m rag_guardbench.sample_data --output-dir data

test:
	$(PYTHON) -m pytest
