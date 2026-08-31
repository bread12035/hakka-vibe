"""Run record tests.

The usage mapping used here was observed on a real call. Both the API response
and a Claude Code session transcript report usage under the same field names,
so one parser serves both adapters.
"""

from decimal import Decimal
from pathlib import Path

import pytest

from hakka_vibe.measurement.cost import TokenCounts
from hakka_vibe.measurement.run_record import (
    Call,
    RunRecord,
    UsageFieldMissing,
    read_run_record,
    token_counts_from_usage,
    write_run_record,
)

OBSERVED_USAGE = {
    "input_tokens": 2,
    "cache_creation_input_tokens": 10_319,
    "cache_read_input_tokens": 222_908,
    "output_tokens": 971,
    "output_tokens_details": {"thinking_tokens": 580},
    "cache_creation": {
        "ephemeral_5m_input_tokens": 0,
        "ephemeral_1h_input_tokens": 10_319,
    },
    "service_tier": "standard",
    "speed": "standard",
}


def test_cache_write_is_read_from_the_ttl_split_not_the_total() -> None:
    # cache_creation_input_tokens (10,319) is the sum of the per-TTL fields.
    # Reading both would charge the write twice, and at the wrong blended rate.
    assert token_counts_from_usage(OBSERVED_USAGE) == TokenCounts(
        input=2,
        output=971,
        thinking=580,
        cache_read=222_908,
        cache_write_5m=0,
        cache_write_1h=10_319,
    )


def test_a_stored_run_record_keeps_the_raw_usage_verbatim(tmp_path: Path) -> None:
    # Which fields matter is not settled yet — thinking_tokens and the TTL split
    # only became interesting once someone looked. Storing a summary would throw
    # away the answer to the next question and cost a re-run of every arm.
    usage = dict(OBSERVED_USAGE, iterations=[{"input_tokens": 2, "output_tokens": 971}])
    record = RunRecord(
        experiment="6",
        arm="6a",
        run=1,
        model="claude-opus-5",
        passed=True,
        calls=(Call(model="claude-opus-5", usage=usage),),
    )

    path = write_run_record(record, root=tmp_path)

    assert read_run_record(path).calls == (Call(model="claude-opus-5", usage=usage),)


def test_run_records_are_filed_under_their_experiment_and_arm(tmp_path: Path) -> None:
    record = RunRecord(
        experiment="6",
        arm="6a",
        run=2,
        model="claude-opus-5",
        passed=False,
        calls=(Call(model="claude-opus-5", usage=OBSERVED_USAGE),),
    )

    path = write_run_record(record, root=tmp_path)

    assert path.relative_to(tmp_path).parts == ("6", "6a", "2.json")


def test_a_run_record_prices_itself_from_its_usage() -> None:
    record = RunRecord(
        experiment="6",
        arm="6a",
        run=1,
        model="claude-opus-5",
        passed=True,
        calls=(Call(model="claude-opus-5", usage=OBSERVED_USAGE),),
    )

    #   input          2 tok * $5.00/MTok  = $0.000010
    #   cache read 222908 tok * $0.50/MTok  = $0.111454
    #   1h write    10319 tok * $10.00/MTok = $0.103190
    #   output        971 tok * $25.00/MTok = $0.024275
    assert record.cost.total == Decimal("0.238929")


def test_a_missing_priced_field_is_an_error_not_a_zero() -> None:
    # A field that silently reads as zero prices that token class at $0: no
    # failure, no warning, and every conclusion drawn from the run is wrong.
    # An upstream rename has to stop the run, not quietly discount it.
    renamed_upstream = {k: v for k, v in OBSERVED_USAGE.items() if k != "cache_read_input_tokens"}

    with pytest.raises(UsageFieldMissing, match="cache_read_input_tokens"):
        token_counts_from_usage(renamed_upstream)


def test_an_absent_detail_object_still_reads_as_zero() -> None:
    # The API reports these as null when there is nothing to report, which is a
    # real answer rather than a missing one.
    quiet_call = dict(OBSERVED_USAGE, output_tokens_details=None, cache_creation=None)

    counts = token_counts_from_usage(quiet_call)

    assert counts.thinking == 0
    assert counts.cache_write_5m == 0
    assert counts.cache_write_1h == 0


def test_a_run_covers_every_call_it_took() -> None:
    # A run is a whole task, not one call. Summing the calls before storing them
    # would lose the per-call detail that shows *where* in a task the cost went.
    record = RunRecord(
        experiment="6",
        arm="6a",
        run=1,
        model="claude-opus-5",
        calls=(
            Call(model="claude-opus-5", usage=OBSERVED_USAGE),
            Call(model="claude-opus-5", usage=OBSERVED_USAGE),
        ),
    )

    assert record.tokens.output == 971 * 2
    assert record.tokens.cache_read == 222_908 * 2
    assert record.cost.total == Decimal("0.238929") * 2
