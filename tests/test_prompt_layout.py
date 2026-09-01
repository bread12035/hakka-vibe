"""Prompt layout tests: experiment 1's actual variable — where a volatile
block sits relative to accumulating history. Pure function, no call needed.
"""

from hakka_vibe.harness.prompt_layout import PromptLayout, assemble_messages

HISTORY = [
    {"role": "user", "content": "task"},
    {"role": "assistant", "content": "turn 1"},
    {"role": "user", "content": "turn 1 result"},
    {"role": "assistant", "content": "turn 2"},
]


def test_baseline_puts_the_dynamic_block_after_all_history() -> None:
    assembled = assemble_messages(HISTORY, "PROGRESS: turn 2 of 40", layout=PromptLayout.BASELINE)

    assert assembled[:-1] == HISTORY
    assert assembled[-1]["content"] == "PROGRESS: turn 2 of 40"


def test_dynamic_first_puts_it_before_any_history() -> None:
    assembled = assemble_messages(
        HISTORY, "PROGRESS: turn 2 of 40", layout=PromptLayout.DYNAMIC_FIRST
    )

    assert assembled[0]["content"] == "PROGRESS: turn 2 of 40"
    assert assembled[1:] == HISTORY


def test_interleaved_repeats_a_stable_reminder_through_the_history() -> None:
    assembled = assemble_messages(
        HISTORY,
        "PROGRESS: turn 2 of 40",
        layout=PromptLayout.STATIC_INTERLEAVED,
        reminder="REMEMBER: small edits",
    )

    reminders = [m for m in assembled if m.get("content") == "REMEMBER: small edits"]
    assert len(reminders) == len(HISTORY) // 2
    assert assembled[-1]["content"] == "PROGRESS: turn 2 of 40"


def test_the_original_history_list_is_never_mutated() -> None:
    original = list(HISTORY)

    assemble_messages(HISTORY, "note", layout=PromptLayout.DYNAMIC_FIRST)

    assert HISTORY == original
