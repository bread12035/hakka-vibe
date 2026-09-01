"""Deriving a tool schema from a callable's own signature and docstring.

Derived rather than hand-written so a schema can't quietly drift away from the
code it describes — a hand-maintained copy stops matching with no error at the
point it happens, only a confusing one later.
"""

import inspect
from typing import Any

from anthropic.types import ToolParam

_JSON_TYPES = {str: "string", int: "integer", bool: "boolean"}

_AMBIENT_PARAMS = {"self", "workspace"}
"""Parameters the model never supplies, because the caller binds them ambiently
rather than the model choosing them: ``self`` for a bound method, ``workspace``
for the free functions this project's agents use instead."""


def schema_of(func: Any) -> ToolParam:
    """Build a tool schema from a function's (or bound/unbound method's)
    signature and docstring."""
    signature = inspect.signature(func)
    hints = inspect.get_annotations(func, eval_str=True)
    properties = {
        name: {"type": _JSON_TYPES[hints[name]]}
        for name in signature.parameters
        if name not in _AMBIENT_PARAMS
    }
    return ToolParam(
        name=func.__name__,
        description=inspect.getdoc(func) or "",
        input_schema={
            "type": "object",
            "properties": properties,
            "required": list(properties),
            "additionalProperties": False,
        },
    )
