from __future__ import annotations

import ast
from typing import Any


FORBIDDEN_STRINGS = (
    "shift(-",
    "future_close",
    "future_return",
    "future_price",
    "future_high",
    "future_low",
    "future_volume",
    "tomorrow",
    "next_candle",
    "lookahead",
    "leverage: true",
    "futures: true",
)

FUTURE_IDENTIFIER_TOKENS = (
    "future_close",
    "future_return",
    "future_price",
    "future_high",
    "future_low",
    "future_volume",
    "next_candle",
    "tomorrow",
    "lookahead",
)


def contains_forbidden_logic(text: str, analyze_python: bool = False) -> list[str]:
    """Return suspicious tokens that suggest future leakage or unsafe execution."""
    lowered = text.lower()
    issues = [token for token in FORBIDDEN_STRINGS if token in lowered]
    if analyze_python or _looks_like_python_source(text):
        ast_review = analyze_python_lookahead_risk(text, strict=False)
        issues.extend(ast_review["risk_patterns"])
    return sorted(set(issues))


def analyze_python_lookahead_risk(source_code: str, strict: bool = True) -> dict[str, Any]:
    """Statically inspect Python source for obvious look-ahead patterns without executing it."""
    warnings: list[str] = []
    risk_patterns: list[str] = []
    try:
        tree = ast.parse(source_code)
    except SyntaxError as exc:
        message = f"Python AST parse failed: {exc.msg}"
        warnings.append(message)
        return {"has_risk": strict, "warnings": warnings, "risk_patterns": [message] if strict else []}

    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and _is_shift_call(node) and _has_negative_shift_arg(node):
            risk_patterns.append(f"negative pandas shift at line {getattr(node, 'lineno', '?')}")
        if isinstance(node, ast.Subscript) and _is_iloc_access(node) and _slice_has_future_offset(node.slice):
            risk_patterns.append(f"future iloc offset at line {getattr(node, 'lineno', '?')}")
        if isinstance(node, ast.Name) and _is_future_identifier(node.id):
            risk_patterns.append(f"future-looking identifier '{node.id}' at line {getattr(node, 'lineno', '?')}")
        if isinstance(node, ast.Attribute) and _is_future_identifier(node.attr):
            risk_patterns.append(f"future-looking attribute '{node.attr}' at line {getattr(node, 'lineno', '?')}")

    return {"has_risk": bool(risk_patterns), "warnings": warnings, "risk_patterns": sorted(set(risk_patterns))}


def validate_generated_code_safety(code: str) -> tuple[bool, list[str]]:
    """Validate generated strategy code for first-layer look-ahead and execution safety."""
    issues = contains_forbidden_logic(code, analyze_python=True)
    lowered = code.lower()
    if "can_short = true" in lowered:
        issues.append("can_short = true")
    if "return 1.0" not in lowered and "def leverage" in lowered:
        issues.append("leverage override does not visibly return 1.0")
    return not issues, issues


def _looks_like_python_source(text: str) -> bool:
    lowered = text.lower()
    return any(token in lowered for token in ("def ", "class ", "import ", "dataframe", ".shift", ".iloc"))


def _is_shift_call(node: ast.Call) -> bool:
    return isinstance(node.func, ast.Attribute) and node.func.attr == "shift"


def _has_negative_shift_arg(node: ast.Call) -> bool:
    if node.args and _is_negative_numeric(node.args[0]):
        return True
    for keyword in node.keywords:
        if keyword.arg in {"periods", "n"} and _is_negative_numeric(keyword.value):
            return True
    return False


def _is_negative_numeric(node: ast.AST) -> bool:
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value < 0
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
        return isinstance(node.operand, ast.Constant) and isinstance(node.operand.value, (int, float))
    return False


def _is_iloc_access(node: ast.Subscript) -> bool:
    value = node.value
    return isinstance(value, ast.Attribute) and value.attr == "iloc"


def _slice_has_future_offset(node: ast.AST) -> bool:
    if isinstance(node, ast.Tuple):
        return any(_slice_has_future_offset(element) for element in node.elts)
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        return (
            _contains_index_name(node.left)
            and _is_future_offset_operand(node.right)
            or _contains_index_name(node.right)
            and _is_future_offset_operand(node.left)
        )
    return False


def _contains_index_name(node: ast.AST) -> bool:
    if isinstance(node, ast.Name):
        return node.id.lower() in {"i", "idx", "index", "current_index", "row_index", "candle_index"}
    return any(_contains_index_name(child) for child in ast.iter_child_nodes(node))


def _is_positive_numeric(node: ast.AST) -> bool:
    return isinstance(node, ast.Constant) and isinstance(node.value, (int, float)) and node.value > 0


def _is_future_offset_operand(node: ast.AST) -> bool:
    if _is_positive_numeric(node):
        return True
    return isinstance(node, ast.Name) and node.id.lower() not in {
        "i",
        "idx",
        "index",
        "current_index",
        "row_index",
        "candle_index",
    }


def _is_future_identifier(identifier: str) -> bool:
    lowered = identifier.lower()
    return any(token in lowered for token in FUTURE_IDENTIFIER_TOKENS)


def assert_research_only(config: dict[str, Any]) -> None:
    safety = config.get("safety", {})
    if safety.get("live_trading_enabled") or safety.get("real_orders_enabled"):
        raise ValueError("Live real-money trading must remain disabled in v1.")
    if safety.get("leverage_enabled") or safety.get("futures_enabled"):
        raise ValueError("Leverage and futures must remain disabled by default.")
