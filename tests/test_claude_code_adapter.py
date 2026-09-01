"""Claude Code transcript adapter tests. No credentials needed: this parses an
already-recorded transcript.
"""

import json
from pathlib import Path
from typing import Any

from hakka_vibe.measurement.claude_code_adapter import run_record_from_transcript

ASSISTANT_LINE_1 = {
    "type": "assistant",
    "message": {
        "model": "claude-opus-5",
        "usage": {
            "input_tokens": 2,
            "cache_creation_input_tokens": 10_319,
            "cache_read_input_tokens": 222_908,
            "output_tokens": 971,
            "output_tokens_details": {"thinking_tokens": 580},
            "cache_creation": {
                "ephemeral_5m_input_tokens": 0,
                "ephemeral_1h_input_tokens": 10_319,
            },
        },
    },
}

ASSISTANT_LINE_2_DIFFERENT_MODEL = {
    "type": "assistant",
    "message": {
        "model": "claude-sonnet-5",
        "usage": {
            "input_tokens": 5,
            "cache_creation_input_tokens": 0,
            "cache_read_input_tokens": 100,
            "output_tokens": 40,
            "output_tokens_details": {"thinking_tokens": 0},
            "cache_creation": {"ephemeral_5m_input_tokens": 0, "ephemeral_1h_input_tokens": 0},
        },
    },
}

NON_USAGE_LINES = [
    {"type": "user", "message": {"role": "user", "content": "hi"}},
    {"type": "queue-operation", "op": "clear"},
]


def write_transcript(path: Path, lines: list[Any]) -> Path:
    path.write_text("\n".join(json.dumps(line) for line in lines))
    return path


def test_every_assistant_call_in_the_transcript_becomes_a_call(tmp_path: Path) -> None:
    transcript = write_transcript(
        tmp_path / "session.jsonl", [ASSISTANT_LINE_1, ASSISTANT_LINE_2_DIFFERENT_MODEL]
    )

    record = run_record_from_transcript(transcript, experiment="1", arm="1d", run=1, passed=True)

    assert len(record.calls) == 2
    assert record.calls[0].model == "claude-opus-5"
    assert record.calls[1].model == "claude-sonnet-5"


def test_non_usage_lines_are_skipped_not_misread_as_zero_cost_calls(tmp_path: Path) -> None:
    transcript = write_transcript(
        tmp_path / "session.jsonl", [*NON_USAGE_LINES, ASSISTANT_LINE_1, *NON_USAGE_LINES]
    )

    record = run_record_from_transcript(transcript, experiment="1", arm="1d", run=1, passed=True)

    assert len(record.calls) == 1


def test_cache_write_ttl_split_survives_the_round_trip(tmp_path: Path) -> None:
    transcript = write_transcript(tmp_path / "session.jsonl", [ASSISTANT_LINE_1])

    record = run_record_from_transcript(transcript, experiment="1", arm="1d", run=1, passed=True)

    assert record.tokens.cache_write_1h == 10_319
    assert record.tokens.cache_write_5m == 0
