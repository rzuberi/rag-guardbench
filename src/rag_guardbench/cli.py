from __future__ import annotations

import argparse
from pathlib import Path

from rag_guardbench.pipeline import run_benchmark
from rag_guardbench.retrieval import SUPPORTED_RETRIEVERS
from rag_guardbench.sample_data import generate_dataset


def main() -> None:
    parser = argparse.ArgumentParser(description="Run RAG-GuardBench.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    generate_parser = subparsers.add_parser("generate-data", help="Generate the sample corpus and benchmark cases.")
    generate_parser.add_argument("--output-dir", type=Path, default=Path("data"))

    run_parser = subparsers.add_parser("run", help="Run the benchmark and write reports.")
    run_parser.add_argument("--corpus", type=Path, default=Path("data/corpus.json"))
    run_parser.add_argument("--cases", type=Path, default=Path("data/cases.json"))
    run_parser.add_argument("--output-dir", type=Path, default=Path("artifacts"))
    run_parser.add_argument("--backend", choices=["mock", "openai"], default="mock")
    run_parser.add_argument("--retriever", choices=SUPPORTED_RETRIEVERS, default="tfidf")
    run_parser.add_argument("--top-k", type=int, default=4)

    args = parser.parse_args()
    if args.command == "generate-data":
        generate_dataset(args.output_dir)
        return
    if args.top_k < 1:
        parser.error("--top-k must be at least 1")
    run_benchmark(
        args.corpus,
        args.cases,
        args.output_dir,
        backend=args.backend,
        retriever_name=args.retriever,
        top_k=args.top_k,
    )


if __name__ == "__main__":
    main()
