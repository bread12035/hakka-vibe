"""The second adapter into RunRecord's seam: a Claude Code session transcript.

Two real adapters — this one and the raw API response every self-built-harness
agent already produces — are what make RunRecord construction a genuine seam
rather than a hypothetical one. Both report usage under the same field names,
which is what lets token_counts_from_usage serve either without a switch.

Claude Code writes cache at a fixed 1 hour TTL — its own behaviour, not
something this project configures — so results built from this adapter are
never compared against self-built-harness percentages in the same table.
"""

import json
from pathlib import Path
from typing import Any

from hakka_vibe.measurement.run_record import Call, RunRecord


def _assistant_messages(transcript: Path) -> list[dict[str, Any]]:
    """Every assistant message in a transcript, in order, regardless of content."""
    messages = []
    for raw_line in transcript.read_text().splitlines():
        if not raw_line.strip():
            continue
        entry = json.loads(raw_line)
        if entry.get("type") == "assistant":
            messages.append(entry.get("message") or {})
    return messages


def _assistant_usage_lines(transcript: Path) -> list[dict[str, Any]]:
    """Only the assistant messages that carry usage — a transcript also holds
    user turns and queue events, which must be skipped, not misread as
    zero-cost calls."""
    return [message for message in _assistant_messages(transcript) if message.get("usage")]


def final_assistant_text(transcript: Path) -> str:
    """The text of the last assistant turn that said anything at all.

    A session's final turn is often tool-use only (a last bash call with no
    prose), so the answer to grade lives on the last turn with text, not
    necessarily the last turn overall.
    """
    for message in reversed(_assistant_messages(transcript)):
        blocks = message.get("content") or []
        text = "\n".join(block["text"] for block in blocks if block.get("type") == "text")
        if text:
            return text
    return ""


def run_record_from_transcript(
    transcript: Path, *, experiment: str, arm: str, run: int, passed: bool | None
) -> RunRecord:
    """Build a run record from one Claude Code session transcript.

    One session is one run: every call in the transcript becomes a call in
    the record, each priced at the model that actually produced it.
    """
    messages = _assistant_usage_lines(transcript)
    calls = tuple(Call(model=message["model"], usage=message["usage"]) for message in messages)
    model = messages[-1]["model"] if messages else ""
    return RunRecord(
        experiment=experiment, arm=arm, run=run, model=model, calls=calls, passed=passed
    )
