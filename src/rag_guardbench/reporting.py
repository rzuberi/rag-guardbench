from __future__ import annotations

import html
import json
from collections import defaultdict
from pathlib import Path

from rag_guardbench.schemas import CaseResult


def percentage(value: float) -> str:
    return f"{100.0 * value:.1f}%"


def summarize(results: list[CaseResult], backend: str) -> dict[str, object]:
    grouped: dict[str, list[CaseResult]] = defaultdict(list)
    attacks_only: dict[str, list[CaseResult]] = defaultdict(list)
    benign_only: dict[str, list[CaseResult]] = defaultdict(list)
    for result in results:
        grouped[result.setting].append(result)
        if result.attack_present:
            attacks_only[result.setting].append(result)
        else:
            benign_only[result.setting].append(result)

    per_setting: list[dict[str, object]] = []
    for setting, setting_results in grouped.items():
        attack_results = attacks_only[setting]
        benign_results = benign_only[setting]
        attack_success_rate = (
            sum(item.attack_success for item in attack_results) / len(attack_results)
            if attack_results
            else 0.0
        )
        safe_answer_rate = sum(item.safe_answer for item in setting_results) / len(setting_results)
        tool_misuse_rate = sum(item.unsafe_tool_attempted for item in setting_results) / len(setting_results)
        defense_win_rate = (
            sum(item.defense_win for item in attack_results) / len(attack_results)
            if attack_results
            else 0.0
        )
        overblocking_rate = (
            sum(item.overblocked for item in benign_results) / len(benign_results)
            if benign_results
            else 0.0
        )
        per_setting.append(
            {
                "setting": setting,
                "attack_success_rate": round(attack_success_rate, 4),
                "safe_answer_rate": round(safe_answer_rate, 4),
                "tool_misuse_rate": round(tool_misuse_rate, 4),
                "defense_win_rate": round(defense_win_rate, 4),
                "overblocking_rate": round(overblocking_rate, 4),
                "num_cases": len(setting_results),
            }
        )

    category_rows: list[dict[str, object]] = []
    for setting, setting_results in grouped.items():
        category_groups: dict[str, list[CaseResult]] = defaultdict(list)
        for result in setting_results:
            category_groups[result.attack_category].append(result)
        for category, category_results in sorted(category_groups.items()):
            category_rows.append(
                {
                    "setting": setting,
                    "attack_category": category,
                    "attack_success_rate": round(
                        sum(item.attack_success for item in category_results if item.attack_present)
                        / max(sum(item.attack_present for item in category_results), 1),
                        4,
                    ),
                    "safe_answer_rate": round(
                        sum(item.safe_answer for item in category_results) / len(category_results),
                        4,
                    ),
                    "tool_misuse_rate": round(
                        sum(item.unsafe_tool_attempted for item in category_results) / len(category_results),
                        4,
                    ),
                }
            )

    failures: list[dict[str, object]] = []
    seen_categories: dict[str, int] = defaultdict(int)
    for result in results:
        if not (result.attack_success or result.overblocked or result.unsafe_tool_attempted):
            continue
        if seen_categories[result.attack_category] >= 2:
            continue
        failures.append(result.to_dict())
        seen_categories[result.attack_category] += 1
        if len(failures) >= 15:
            break
    return {
        "backend": backend,
        "num_settings": len(per_setting),
        "num_cases": len({result.case_id for result in results}),
        "settings": per_setting,
        "category_breakdown": category_rows,
        "selected_failures": failures,
    }


def write_bar_chart(path: Path, rows: list[dict[str, object]], key: str, title: str) -> None:
    width = 760
    height = 320
    margin = 70
    chart_width = width - 2 * margin
    chart_height = height - 2 * margin
    bar_width = chart_width / max(len(rows), 1) * 0.65
    max_value = 1.0
    labels = [row["setting"] for row in rows]
    bars: list[str] = []
    for index, row in enumerate(rows):
        value = float(row[key])
        x = margin + index * (chart_width / max(len(rows), 1)) + 12
        bar_height = chart_height * value / max_value
        y = height - margin - bar_height
        bars.append(
            f'<rect x="{x:.1f}" y="{y:.1f}" width="{bar_width:.1f}" height="{bar_height:.1f}" fill="#0f766e" />'
        )
        bars.append(
            f'<text x="{x + bar_width / 2:.1f}" y="{y - 8:.1f}" text-anchor="middle" font-size="12">{value:.2f}</text>'
        )
        bars.append(
            f'<text x="{x + bar_width / 2:.1f}" y="{height - margin + 18:.1f}" text-anchor="middle" font-size="11">{labels[index]}</text>'
        )
    axes = (
        f'<line x1="{margin}" y1="{height - margin}" x2="{width - margin}" y2="{height - margin}" stroke="#334155" stroke-width="1.5" />'
        f'<line x1="{margin}" y1="{margin}" x2="{margin}" y2="{height - margin}" stroke="#334155" stroke-width="1.5" />'
    )
    ticks = []
    for step in range(6):
        tick_value = step / 5
        y = height - margin - chart_height * tick_value
        ticks.append(f'<line x1="{margin - 4}" y1="{y:.1f}" x2="{margin}" y2="{y:.1f}" stroke="#334155" />')
        ticks.append(f'<text x="{margin - 10}" y="{y + 4:.1f}" text-anchor="end" font-size="11">{tick_value:.1f}</text>')
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
<rect width="100%" height="100%" fill="#f8fafc" />
<text x="{width/2:.1f}" y="30" text-anchor="middle" font-size="18" font-weight="600">{html.escape(title)}</text>
{axes}
{''.join(ticks)}
{''.join(bars)}
</svg>
"""
    path.write_text(svg)


def build_markdown(summary: dict[str, object]) -> str:
    lines = [
        "# RAG-GuardBench Report",
        "",
        f"Backend: `{summary['backend']}`",
        "",
        f"Cases: `{summary['num_cases']}` across `{summary['num_settings']}` settings.",
        "",
        "## Summary Table",
        "",
        "| Setting | Attack success | Safe answer | Tool misuse | Defense win | Overblocking |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in summary["settings"]:
        lines.append(
            f"| `{row['setting']}` | `{row['attack_success_rate']:.2f}` | `{row['safe_answer_rate']:.2f}` | `{row['tool_misuse_rate']:.2f}` | `{row['defense_win_rate']:.2f}` | `{row['overblocking_rate']:.2f}` |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "The insecure baseline is intentionally vulnerable to instruction-following from retrieved text, answer poisoning, and unsafe tool triggers.",
            "Prompt hardening and sanitization reduce document-instruction compliance, while two-stage answering is especially effective against poisoned context.",
            "The full guard combines untrusted-context prompting, sanitization, staged fact extraction, and tool gating to reduce attack success without heavily overblocking benign tasks.",
            "",
            "## Selected Failure Examples",
            "",
        ]
    )
    for failure in summary["selected_failures"][:8]:
        lines.extend(
            [
                f"### `{failure['case_id']}` under `{failure['setting']}`",
                "",
                f"- attack category: `{failure['attack_category']}`",
                f"- attack success: `{failure['attack_success']}`",
                f"- unsafe tool attempted: `{failure['unsafe_tool_attempted']}`",
                f"- leaked protected value: `{failure['leaked_protected_value']}`",
                f"- answer: {failure['answer']}",
                "",
            ]
        )
    return "\n".join(lines) + "\n"


def build_html(summary: dict[str, object]) -> str:
    rows = []
    for row in summary["settings"]:
        rows.append(
            "<tr>"
            f"<td><code>{html.escape(str(row['setting']))}</code></td>"
            f"<td>{row['attack_success_rate']:.2f}</td>"
            f"<td>{row['safe_answer_rate']:.2f}</td>"
            f"<td>{row['tool_misuse_rate']:.2f}</td>"
            f"<td>{row['defense_win_rate']:.2f}</td>"
            f"<td>{row['overblocking_rate']:.2f}</td>"
            "</tr>"
        )
    failures = []
    for failure in summary["selected_failures"][:8]:
        failures.append(
            "<article class='failure'>"
            f"<h3><code>{html.escape(str(failure['case_id']))}</code> under <code>{html.escape(str(failure['setting']))}</code></h3>"
            f"<p><strong>Category:</strong> {html.escape(str(failure['attack_category']))}</p>"
            f"<p><strong>Attack success:</strong> {html.escape(str(failure['attack_success']))}</p>"
            f"<p><strong>Answer:</strong> {html.escape(str(failure['answer']))}</p>"
            "</article>"
        )
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <title>RAG-GuardBench Report</title>
  <style>
    body {{ font-family: Georgia, "Times New Roman", serif; margin: 2rem auto; max-width: 980px; color: #172033; background: #f8fafc; }}
    h1, h2, h3 {{ color: #0f172a; }}
    table {{ border-collapse: collapse; width: 100%; margin: 1rem 0 2rem; }}
    th, td {{ border: 1px solid #cbd5e1; padding: 0.65rem 0.8rem; text-align: left; }}
    th {{ background: #e2e8f0; }}
    .failure {{ background: white; border: 1px solid #cbd5e1; padding: 1rem; margin-bottom: 1rem; }}
  </style>
</head>
<body>
  <h1>RAG-GuardBench Report</h1>
  <p>Backend: <code>{html.escape(str(summary['backend']))}</code></p>
  <p>Cases: <code>{summary['num_cases']}</code> across <code>{summary['num_settings']}</code> settings.</p>
  <h2>Summary Table</h2>
  <table>
    <thead>
      <tr><th>Setting</th><th>Attack success</th><th>Safe answer</th><th>Tool misuse</th><th>Defense win</th><th>Overblocking</th></tr>
    </thead>
    <tbody>
      {''.join(rows)}
    </tbody>
  </table>
  <h2>Selected Failure Examples</h2>
  {''.join(failures)}
</body>
</html>
"""


def build_reports(results: list[CaseResult], output_dir: Path, backend: str) -> dict[str, object]:
    summary = summarize(results, backend)
    docs_dir = output_dir.parent / "docs"
    figures_dir = docs_dir / "figures"
    docs_dir.mkdir(parents=True, exist_ok=True)
    figures_dir.mkdir(parents=True, exist_ok=True)
    summary_path = output_dir / "summary.json"
    markdown_path = docs_dir / "benchmark_report.md"
    html_path = docs_dir / "benchmark_report.html"
    summary_path.write_text(json.dumps(summary, indent=2) + "\n")
    markdown_path.write_text(build_markdown(summary))
    html_path.write_text(build_html(summary))
    write_bar_chart(figures_dir / "attack_success_by_setting.svg", summary["settings"], "attack_success_rate", "Attack Success Rate by Setting")
    write_bar_chart(figures_dir / "tool_misuse_by_setting.svg", summary["settings"], "tool_misuse_rate", "Tool Misuse Rate by Setting")
    write_bar_chart(figures_dir / "overblocking_by_setting.svg", summary["settings"], "overblocking_rate", "Benign Overblocking by Setting")
    return summary
