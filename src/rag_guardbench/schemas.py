from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class Document:
    doc_id: str
    title: str
    source: str
    topic: str
    kind: str
    text: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class BenchmarkCase:
    case_id: str
    topic: str
    query: str
    attack_category: str
    attack_present: bool
    document_ids: list[str]
    expected_answer: str
    safe_answer_keywords: list[str]
    forbidden_terms: list[str]
    protected_values: list[str]
    allowed_tools: list[str]
    expected_safe_behavior: str
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Chunk:
    chunk_id: str
    doc_id: str
    title: str
    topic: str
    kind: str
    text: str
    score: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ToolCall:
    name: str
    arguments: dict[str, Any]
    justification: str
    allowed: bool = False
    executed: bool = False
    output: str = ""
    blocked_reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class DefenseSetting:
    name: str
    prompt_hardening: bool = False
    context_sanitization: bool = False
    two_stage_answering: bool = False
    tool_permission_gating: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class CaseResult:
    case_id: str
    setting: str
    attack_category: str
    attack_present: bool
    answer: str
    safe_answer: bool
    corrupted_answer: bool
    leaked_protected_value: bool
    unsafe_tool_attempted: bool
    unsafe_tool_executed: bool
    attack_success: bool
    defense_win: bool
    overblocked: bool
    retrieved_doc_ids: list[str]
    retrieved_chunk_ids: list[str]
    defense_actions: list[str]
    tool_calls: list[dict[str, Any]]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

