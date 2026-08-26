"""Smoke test for the run entry point.

Exactly one test lives here, because every execution costs a real call. The
pricing and parsing this exercises are covered by fast tests elsewhere; what
this proves is only that the whole path joins up.
"""

import os
from pathlib import Path

import pytest

from hakka_vibe.call import record_one_call_to_disk
from hakka_vibe.run_record import read_run_record

pytestmark = pytest.mark.skipif(
    not os.environ.get("ANTHROPIC_API_KEY"),
    reason="needs credentials: this test makes a real, billable call",
)


def test_one_call_lands_on_disk_priced(tmp_path: Path) -> None:
    from anthropic import Anthropic

    path = record_one_call_to_disk(
        Anthropic(),
        prompt="Reply with the single word: ok",
        model="claude-haiku-4-5",
        experiment="smoke",
        arm="smoke",
        run=1,
        root=tmp_path,
    )

    record = read_run_record(path)
    assert record.tokens.input > 0
    assert record.tokens.output > 0
    assert record.cost.total > 0
