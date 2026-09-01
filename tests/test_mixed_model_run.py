"""A run can span more than one model.

A Claude Code session can switch models mid-conversation. A run recorded from
such a transcript must price each call at the model that produced it, not the
run's nominal model applied to the summed tokens.
"""

from decimal import Decimal

from hakka_vibe.measurement.run_record import Call, RunRecord

ONE_MILLION_INPUT = {
    "input_tokens": 1_000_000,
    "output_tokens": 0,
    "output_tokens_details": None,
    "cache_read_input_tokens": 0,
    "cache_creation": None,
}


def test_each_call_is_priced_at_the_model_that_produced_it() -> None:
    # 1M input on Opus 5 ($5.00/MTok) plus 1M on Sonnet 5 ($2.00/MTok). Pricing
    # the whole run at one model would over- or under-charge whichever calls
    # actually ran on the other.
    record = RunRecord(
        experiment="6",
        arm="6a",
        run=1,
        model="claude-opus-5",
        calls=(
            Call(model="claude-opus-5", usage=ONE_MILLION_INPUT),
            Call(model="claude-sonnet-5", usage=ONE_MILLION_INPUT),
        ),
    )

    assert record.cost.total == Decimal("5.00") + Decimal("2.00")
