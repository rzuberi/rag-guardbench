from __future__ import annotations

from dataclasses import dataclass

from rag_guardbench.schemas import ToolCall


SAFE_TOOLS = {"calculator"}


@dataclass
class ToolContext:
    retrieved_context: str
    internal_notes: str


def execute_tool(tool_call: ToolCall, context: ToolContext) -> str:
    if tool_call.name == "calculator":
        expression = str(tool_call.arguments.get("expression", ""))
        allowed = set("0123456789+-*/(). ")
        if expression and set(expression) <= allowed:
            return str(eval(expression, {"__builtins__": {}}, {}))
        return "invalid_expression"
    if tool_call.name == "export_context":
        return context.retrieved_context
    if tool_call.name == "lookup_internal_notes":
        return context.internal_notes
    if tool_call.name == "send_report":
        return "report_sent"
    return "unknown_tool"


def apply_tool_policy(
    tool_calls: list[ToolCall],
    gating_enabled: bool,
    user_query: str,
    context: ToolContext,
) -> list[ToolCall]:
    final_calls: list[ToolCall] = []
    query_tokens = {token for token in user_query.lower().split() if len(token) > 2}
    for tool_call in tool_calls:
        if not gating_enabled:
            tool_call.allowed = True
            tool_call.executed = True
            tool_call.output = execute_tool(tool_call, context)
            final_calls.append(tool_call)
            continue
        if tool_call.name in SAFE_TOOLS:
            tool_call.allowed = True
            tool_call.executed = True
            tool_call.output = execute_tool(tool_call, context)
            final_calls.append(tool_call)
            continue
        justification_tokens = {token for token in tool_call.justification.lower().split() if len(token) > 2}
        if query_tokens & justification_tokens and "internal" not in justification_tokens:
            tool_call.allowed = True
            tool_call.executed = True
            tool_call.output = execute_tool(tool_call, context)
        else:
            tool_call.blocked_reason = "tool_permission_gating"
        final_calls.append(tool_call)
    return final_calls

