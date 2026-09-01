"""Running model-written Python against a namespace that persists across turns.

The analyst agent acts by writing code rather than emitting one tool call per
operation. A shared namespace is what makes that pay off: a result derived on
one turn stays live for the next, instead of being re-queried or
re-serialized into the prompt.
"""

import contextlib
import io
import traceback
from typing import Any


def execute_python(code: str, *, namespace: dict[str, Any]) -> str:
    """Run ``code`` in ``namespace`` and return what it printed.

    ``namespace`` is mutated in place — it's the caller's to keep across
    calls; reusing the same dict on the next turn is what carries state
    forward.

    Exceptions are reported as text, not raised: raising would end the turn
    with no way for the model to see what went wrong and retry.
    """
    output = io.StringIO()
    try:
        with contextlib.redirect_stdout(output):
            exec(code, namespace)  # noqa: S102 — this *is* the agent's execution capability
    except Exception:  # noqa: BLE001 — a REPL for model-written code must survive any exception it raises
        return traceback.format_exc()
    return output.getvalue().strip()
