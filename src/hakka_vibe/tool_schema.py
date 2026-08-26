"""Deriving a tool schema from a method's signature.

Derived rather than hand-written so the schema cannot drift away from the code
it describes: a hand-maintained copy silently stops matching (nooa-design:
"Hand-written JSON schema for tools" is an anti-pattern to replace with type
annotations).
"""

import inspect
from typing import Any

from anthropic.types import ToolParam

_JSON_TYPES = {str: "string", int: "integer", bool: "boolean"}


def schema_of(method: Any) -> ToolParam:
    """Build a tool schema from a bound or unbound method's signature and docstring."""
    signature = inspect.signature(method)
    hints = inspect.get_annotations(method, eval_str=True)
    properties = {
        name: {"type": _JSON_TYPES[hints[name]]} for name in signature.parameters if name != "self"
    }
    return ToolParam(
        name=method.__name__,
        description=inspect.getdoc(method) or "",
        input_schema={
            "type": "object",
            "properties": properties,
            "required": list(properties),
            "additionalProperties": False,
        },
    )
