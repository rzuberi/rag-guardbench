from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


def test_cli_generates_reports(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    output_dir = tmp_path / "artifacts"
    docs_dir = tmp_path / "docs"
    subprocess.run(
        [sys.executable, "-m", "rag_guardbench.cli", "generate-data", "--output-dir", str(data_dir)],
        check=True,
        cwd=ROOT,
    )
    subprocess.run(
        [
            sys.executable,
            "-m",
            "rag_guardbench.cli",
            "run",
            "--corpus",
            str(data_dir / "corpus.json"),
            "--cases",
            str(data_dir / "cases.json"),
            "--output-dir",
            str(output_dir),
            "--retriever",
            "bm25",
            "--top-k",
            "3",
        ],
        check=True,
        cwd=ROOT,
    )
    summary = json.loads((output_dir / "summary.json").read_text())
    manifest = json.loads((output_dir / "run_manifest.json").read_text())
    setting_rows = {row["setting"]: row for row in summary["settings"]}
    assert (output_dir / "case_outcomes.csv").exists()
    assert (output_dir / "run_traces.jsonl").exists()
    assert (docs_dir / "benchmark_report.md").exists()
    assert manifest["retriever"] == "bm25"
    assert manifest["top_k"] == 3
    assert setting_rows["full_guard"]["attack_success_rate"] < setting_rows["baseline_insecure"]["attack_success_rate"]
    assert setting_rows["full_guard"]["tool_misuse_rate"] < setting_rows["baseline_insecure"]["tool_misuse_rate"]
