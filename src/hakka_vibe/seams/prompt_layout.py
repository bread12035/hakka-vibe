"""Experiment 1: where the dynamic block sits relative to accumulating history.

The static block (the frozen system prompt) is unaffected by any of this — the
API always renders tools -> system -> messages, and a seam for that ordering
would have no adapter to place it at. What this project's harness actually
controls is where a volatile, per-turn block sits inside ``messages``, and this
is a pure function so the placement can be pinned down without a call.
"""

from collections.abc import Mapping, Sequence
from enum import Enum
from typing import Any


class PromptLayout(Enum):
    """Arm 1a-1c's variable."""

    BASELINE = "1a"
    """static -> history -> dynamic. The dynamic note is newest, so it sits
    last and every prior byte stays a stable, cacheable prefix."""

    DYNAMIC_FIRST = "1b"
    """dynamic -> history. The volatile block leads, sitting inside what would
    otherwise be the stable prefix — every turn's change invalidates
    everything after it."""

    STATIC_INTERLEAVED = "1c"
    """A stable reminder repeated between each historical turn. Once inserted,
    it changes every byte from that point on relative to what was cached
    before — it can only help a fresh conversation, never a continuing one."""


def _note(text: str) -> dict[str, Any]:
    return {"role": "user", "content": text}


def assemble_messages(
    history: Sequence[Mapping[str, Any]],
    dynamic_note: str,
    *,
    layout: PromptLayout,
    reminder: str = "",
) -> list[dict[str, Any]]:
    """Arrange history and the dynamic note per ``layout``. Never mutates ``history``."""
    if layout is PromptLayout.BASELINE:
        return [*(dict(m) for m in history), _note(dynamic_note)]
    if layout is PromptLayout.DYNAMIC_FIRST:
        return [_note(dynamic_note), *(dict(m) for m in history)]
    # STATIC_INTERLEAVED: insert the reminder after every second history entry.
    interleaved: list[dict[str, Any]] = []
    for index, message in enumerate(history, start=1):
        interleaved.append(dict(message))
        if index % 2 == 0:
            interleaved.append(_note(reminder))
    interleaved.append(_note(dynamic_note))
    return interleaved
