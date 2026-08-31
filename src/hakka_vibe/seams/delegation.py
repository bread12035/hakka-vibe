"""Delegation context: experiment 3's variable.

What varies between arms 3a-3c is only what context reaches the subagent on
each delegation call — never the subagent's own capabilities, which stay
identical across arms (see hakka_vibe.agents.subagent.Subagent).
"""

from collections.abc import Sequence
from enum import Enum


class DelegationMode(Enum):
    """Arm 3a-3c's variable: what a delegation call sends as context."""

    FRESH_FULL = "3a"
    """A brand new subagent every call, given the complete history each time —
    it has no memory of its own, so the whole thing travels with every ask."""

    FRESH_COMPRESSED = "3b"
    """A brand new subagent every call, given only a summary the orchestrator
    already compressed. The compression's own cost belongs to this arm, not
    the subagent's call — see ADR-0002."""

    PERSISTENT = "3c"
    """One subagent object across every call in a run. Only the first call
    needs the full history; later calls send just what is new since the last
    one, because the subagent's own conversation already holds the rest."""


def context_for_call(
    history: Sequence[str],
    *,
    mode: DelegationMode,
    call_index: int,
    compressed: str | None = None,
    new_turns: Sequence[str] = (),
) -> list[str]:
    """What one delegation call sends, given the mode and how far in it is.

    Pure function of the mode and the caller's bookkeeping — no subagent state
    is needed to answer this, which is what makes it testable without a call.
    """
    if mode is DelegationMode.FRESH_FULL:
        return list(history)
    if mode is DelegationMode.FRESH_COMPRESSED:
        return [compressed] if compressed is not None else []
    # PERSISTENT
    return list(history) if call_index == 0 else list(new_turns)
