"""Experiment 1's variable: where a volatile, per-turn note sits relative to
accumulating conversation history.

The frozen system prompt is unaffected by any of this — the API always
renders tools -> system -> messages, and there is no second adapter that would
make a seam for *that* ordering real. What this harness actually controls is
where the dynamic note sits inside ``messages``, and that's a pure function,
testable without a call.
"""

from collections.abc import Mapping, Sequence
from enum import Enum
from typing import Any


class PromptLayout(Enum):
    """Arms 1a-1c."""

    BASELINE = "1a"
    """static -> history -> dynamic. The note is newest, so it sits last and
    every prior byte stays a stable, cacheable prefix."""

    DYNAMIC_FIRST = "1b"
    """dynamic -> history. The volatile block leads, sitting inside what would
    otherwise be the stable prefix — every turn invalidates everything after
    it."""

    STATIC_INTERLEAVED = "1c"
    """A stable reminder repeated between history turns. Once inserted it
    changes every byte after it relative to what was cached before — helps a
    fresh conversation, never a continuing one."""


def _note(text: str) -> dict[str, Any]:
    return {"role": "user", "content": text}


def assemble_messages(
    history: Sequence[Mapping[str, Any]],
    dynamic_note: str,
    *,
    layout: PromptLayout,
    reminder: str = "",
) -> list[dict[str, Any]]:
    """Arrange ``history`` and ``dynamic_note`` per ``layout``. Never mutates ``history``."""
    if layout is PromptLayout.BASELINE:
        return [*(dict(m) for m in history), _note(dynamic_note)]
    if layout is PromptLayout.DYNAMIC_FIRST:
        return [_note(dynamic_note), *(dict(m) for m in history)]

    interleaved: list[dict[str, Any]] = []
    for index, message in enumerate(history, start=1):
        interleaved.append(dict(message))
        if index % 2 == 0:
            interleaved.append(_note(reminder))
    interleaved.append(_note(dynamic_note))
    return interleaved
