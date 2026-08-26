"""Subagent lifecycle and context-passing tests: what's testable without a call.

Three delegation modes (spec's 3a-3c): fresh + full history, fresh + a
compressed handoff, and persistent (first call full, later calls incremental).
The context each mode actually sends is a pure function of its history and
mode — pinned down here.
"""

from hakka_vibe.subagent import DelegationMode, context_for_call


def test_fresh_full_always_sends_the_complete_history() -> None:
    # 3a: every delegation starts a brand new subagent, so it has no memory of
    # its own — the full history must travel with every call.
    history = ["turn 1", "turn 2", "turn 3"]

    assert context_for_call(history, mode=DelegationMode.FRESH_FULL, call_index=0) == history
    assert context_for_call(history, mode=DelegationMode.FRESH_FULL, call_index=2) == history


def test_fresh_compressed_sends_only_the_supplied_summary() -> None:
    # 3b: the orchestrator has already compressed the history before calling
    # here; this mode's job is just to not also send the raw history alongside it.
    history = ["turn 1", "turn 2", "turn 3"]

    context = context_for_call(
        history,
        mode=DelegationMode.FRESH_COMPRESSED,
        call_index=1,
        compressed="turns 1-2 summarised",
    )

    assert context == ["turns 1-2 summarised"]


def test_persistent_sends_full_history_only_on_the_first_call() -> None:
    # 3c: the subagent object itself carries memory across calls, so only the
    # first call needs the full history — a clean single-variable pair against
    # 3a, which always resends it.
    history = ["turn 1", "turn 2", "turn 3"]

    first_call = context_for_call(history, mode=DelegationMode.PERSISTENT, call_index=0)
    later_call = context_for_call(
        history, mode=DelegationMode.PERSISTENT, call_index=1, new_turns=["turn 3"]
    )

    assert first_call == history
    assert later_call == ["turn 3"]
