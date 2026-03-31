from __future__ import annotations

import json
from pathlib import Path

from rag_guardbench.schemas import BenchmarkCase, Document


def load_documents(path: Path) -> dict[str, Document]:
    payload = json.loads(path.read_text())
    return {item["doc_id"]: Document(**item) for item in payload}


def load_cases(path: Path) -> list[BenchmarkCase]:
    payload = json.loads(path.read_text())
    return [BenchmarkCase(**item) for item in payload]

