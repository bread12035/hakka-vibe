"""Reading the final answer out of a Claude Code transcript.

Needed for arms 2d/2e: grading a Claude Code run means reading what it actually
said, the same way run_record_from_transcript reads what it actually cost.
"""

import json
from pathlib import Path
from typing import Any

from hakka_vibe.measurement.claude_code_adapter import final_assistant_text

ASSISTANT_WITH_TEXT: dict[str, Any] = {
    "type": "assistant",
    "message": {
        "model": "claude-opus-5",
        "content": [{"type": "text", "text": "Let me check.\nANSWER: 42 1234.56"}],
        "usage": {
            "input_tokens": 1,
            "output_tokens": 1,
            "output_tokens_details": None,
            "cache_read_input_tokens": 0,
            "cache_creation": None,
        },
    },
}

ASSISTANT_WITH_TOOL_USE_ONLY = {
    "type": "assistant",
    "message": {
        "model": "claude-opus-5",
        "content": [{"type": "tool_use", "id": "t1", "name": "bash", "input": {}}],
        "usage": ASSISTANT_WITH_TEXT["message"]["usage"],
    },
}


def write_transcript(path: Path, lines: list[Any]) -> Path:
    path.write_text("\n".join(json.dumps(line) for line in lines))
    return path


def test_it_returns_the_text_of_the_last_assistant_turn_that_has_any(tmp_path: Path) -> None:
    # The final turn is often tool-use-only (e.g. one last bash call with no
    # prose); the answer line lives on the last turn that actually said
    # something.
    transcript = write_transcript(
        tmp_path / "session.jsonl", [ASSISTANT_WITH_TEXT, ASSISTANT_WITH_TOOL_USE_ONLY]
    )

    assert "ANSWER: 42 1234.56" in final_assistant_text(transcript)


def test_a_transcript_with_no_text_at_all_yields_an_empty_string(tmp_path: Path) -> None:
    transcript = write_transcript(tmp_path / "session.jsonl", [ASSISTANT_WITH_TOOL_USE_ONLY])

    assert final_assistant_text(transcript) == ""
