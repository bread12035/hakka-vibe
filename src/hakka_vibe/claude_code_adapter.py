"""Turn a Claude Code session transcript into a run record.

The second adapter into RunRecord's seam — the API response is the first — so
this is what makes it a real seam rather than a hypothetical one. Both report
usage under the same field names, which is what one parser (token_counts_from_
usage) serving both depends on.

Claude Code writes cache at the 1 hour TTL exclusively; that is its own
behaviour, not a setting this project controls, and it is why results from
this adapter are never compared against the self-built harness's percentages
(spec, §Harness 與 TTL).
"""

import json
from pathlib import Path
from typing import Any

from hakka_vibe.run_record import Call, RunRecord


def _assistant_usage_lines(transcript: Path) -> list[dict[str, Any]]:
    """Read a transcript and return only the lines that carry model usage.

    A Claude Code transcript mixes many line types — user turns, queue
    operations, system events. Only assistant lines with usage are calls; the
    rest must be skipped outright, not misread as zero-cost calls.
    """
    lines = []
    for raw_line in transcript.read_text().splitlines():
        if not raw_line.strip():
            continue
        entry = json.loads(raw_line)
        if entry.get("type") != "assistant":
            continue
        message = entry.get("message") or {}
        if message.get("usage"):
            lines.append(message)
    return lines


def run_record_from_transcript(
    transcript: Path, *, experiment: str, arm: str, run: int, passed: bool | None
) -> RunRecord:
    """Build a run record from one Claude Code session transcript.

    One session is one run: the whole transcript's calls become the run's
    calls, each priced at the model that actually produced it — a session can
    switch models mid-conversation, confirmed on this project's own history.
    """
    messages = _assistant_usage_lines(transcript)
    calls = tuple(Call(model=message["model"], usage=message["usage"]) for message in messages)
    model = messages[-1]["model"] if messages else ""
    return RunRecord(experiment=experiment, arm=arm, run=run, model=model, calls=calls, passed=passed)
