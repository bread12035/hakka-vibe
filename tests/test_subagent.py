"""Subagent lifecycle and context-passing tests: what's testable without a call.

Three delegation modes (3a-3c): fresh + full history, fresh + a compressed
handoff, and persistent (first call full, later calls incremental). The
context each mode actually sends is a pure function of its history and mode.
"""

from hakka_vibe.agents.subagent import DelegationMode, context_for_call


def test_fresh_full_always_sends_the_complete_history() -> None:
    history = ["turn 1", "turn 2", "turn 3"]

    assert context_for_call(history, mode=DelegationMode.FRESH_FULL, call_index=0) == history
    assert context_for_call(history, mode=DelegationMode.FRESH_FULL, call_index=2) == history


def test_fresh_compressed_sends_only_the_supplied_summary() -> None:
    history = ["turn 1", "turn 2", "turn 3"]

    context = context_for_call(
        history,
        mode=DelegationMode.FRESH_COMPRESSED,
        call_index=1,
        compressed="turns 1-2 summarised",
    )

    assert context == ["turns 1-2 summarised"]


def test_persistent_sends_full_history_only_on_the_first_call() -> None:
    history = ["turn 1", "turn 2", "turn 3"]

    first_call = context_for_call(history, mode=DelegationMode.PERSISTENT, call_index=0)
    later_call = context_for_call(
        history, mode=DelegationMode.PERSISTENT, call_index=1, new_turns=["turn 3"]
    )

    assert first_call == history
    assert later_call == ["turn 3"]
