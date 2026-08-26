"""Prompt layout tests: where the dynamic block sits, and what interspersing does to cache.

Pure function, no call needed. This is experiment 1's actual variable: static
content (the frozen system prompt) is unaffected by any of this — the API
always renders tools -> system -> messages — what these arms vary is where a
volatile block sits relative to the accumulating history inside messages.
"""

from hakka_vibe.prompt_layout import PromptLayout, assemble_messages

HISTORY = [
    {"role": "user", "content": "task"},
    {"role": "assistant", "content": "turn 1"},
    {"role": "user", "content": "turn 1 result"},
    {"role": "assistant", "content": "turn 2"},
]


def test_baseline_puts_the_dynamic_block_after_all_history() -> None:
    # 1a: static -> history -> dynamic. The dynamic note is the newest thing,
    # placed last so every prior byte stays a stable, cacheable prefix.
    assembled = assemble_messages(HISTORY, "PROGRESS: turn 2 of 40", layout=PromptLayout.BASELINE)

    assert assembled[:-1] == HISTORY
    assert assembled[-1]["content"] == "PROGRESS: turn 2 of 40"


def test_dynamic_first_puts_it_before_any_history() -> None:
    # 1b: the volatile block leads, so it sits inside what would otherwise be
    # the stable prefix — every turn's change invalidates everything after it.
    assembled = assemble_messages(
        HISTORY, "PROGRESS: turn 2 of 40", layout=PromptLayout.DYNAMIC_FIRST
    )

    assert assembled[0]["content"] == "PROGRESS: turn 2 of 40"
    assert assembled[1:] == HISTORY


def test_interleaved_repeats_a_stable_reminder_through_the_history() -> None:
    # 1c: a reminder is inserted between each historical turn. Once inserted,
    # every byte from that point on differs from what was cached before it was
    # added, so this only ever helps a *fresh* conversation, never a
    # continuing one.
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
    # A layout that mutates the caller's history in place would make the next
    # turn's cache behaviour depend on which layout ran last.
    original = list(HISTORY)

    assemble_messages(HISTORY, "note", layout=PromptLayout.DYNAMIC_FIRST)

    assert HISTORY == original
