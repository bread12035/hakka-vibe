"""Executing model-written code, per nooa-design capability 3: code as action.

The model acts by writing Python, not by emitting a tool-call per operation. A
shared namespace is what makes that pay off: a result derived on one turn stays
live for the next without re-querying or re-serializing it (nooa-design
patterns.md, "df stays live").
"""

import contextlib
import io
import traceback
from typing import Any


def execute_python(code: str, *, namespace: dict[str, Any]) -> str:
    """Run code in ``namespace`` and return what it printed.

    ``namespace`` is mutated in place and is the caller's to keep across calls;
    passing the same dict on the next turn is what carries state forward.

    Exceptions are reported as text, not raised: a raised exception would end
    the turn with no way for the model to see what went wrong and retry.
    """
    output = io.StringIO()
    try:
        with contextlib.redirect_stdout(output):
            exec(code, namespace)  # noqa: S102 — this is the agent's execution capability
    except Exception:  # noqa: BLE001 — a REPL for model-written code must not crash the agent loop on any exception the code raises
        return traceback.format_exc()
    return output.getvalue().strip()
