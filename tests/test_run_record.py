"""Run record tests.

The usage mapping used here was observed on a real call. Both the API response
and a Claude Code session transcript report usage under the same field names,
so one parser serves both adapters.
"""

from decimal import Decimal

from hakka_vibe.run_record import (
    RunRecord,
    TokenCounts,
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


def test_a_stored_run_record_keeps_the_raw_usage_verbatim(tmp_path) -> None:  # type: ignore[no-untyped-def]
    # Which fields matter is not settled yet — thinking_tokens and the TTL split
    # only became interesting once someone looked. Storing a summary would throw
    # away the answer to the next question and cost a re-run of every arm.
    usage = dict(OBSERVED_USAGE, iterations=[{"input_tokens": 2, "output_tokens": 971}])
    record = RunRecord(
        experiment="6", arm="6a", run=1, model="claude-opus-5", passed=True, usage=usage
    )

    path = write_run_record(record, root=tmp_path)

    assert read_run_record(path).usage == usage


def test_run_records_are_filed_under_their_experiment_and_arm(tmp_path) -> None:  # type: ignore[no-untyped-def]
    record = RunRecord(
        experiment="6",
        arm="6a",
        run=2,
        model="claude-opus-5",
        passed=False,
        usage=OBSERVED_USAGE,
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
        usage=OBSERVED_USAGE,
    )

    #   input          2 tok * $5.00/MTok  = $0.000010
    #   cache read 222908 tok * $0.50/MTok  = $0.111454
    #   1h write    10319 tok * $10.00/MTok = $0.103190
    #   output        971 tok * $25.00/MTok = $0.024275
    assert record.cost.total == Decimal("0.238929")
