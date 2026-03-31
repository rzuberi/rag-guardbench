run:
	python -m rag_guardbench.cli run --output-dir artifacts

generate-data:
	python -m rag_guardbench.sample_data --output-dir data

test:
	python -m pytest

