"""A run can span more than one model.

Confirmed on this very session's own transcript: a Claude Code session can
switch models mid-conversation (observed: claude-opus-5 and claude-sonnet-5
usage lines in one transcript file). A run recorded from such a transcript
must price each call at the model that produced it, not the run's nominal
model applied to the summed tokens.
"""

from decimal import Decimal

from hakka_vibe.run_record import Call, RunRecord

ONE_MILLION_INPUT = {
    "input_tokens": 1_000_000,
    "output_tokens": 0,
    "output_tokens_details": None,
    "cache_read_input_tokens": 0,
    "cache_creation": None,
}


def test_each_call_is_priced_at_the_model_that_produced_it() -> None:
    # 1M input tokens on Opus 5 ($5.00/MTok) plus 1M on Sonnet 5 ($2.00/MTok).
    # Pricing the whole run at "opus" would report $10.00, overcharging the
    # sonnet call by 2.5x; pricing it at "sonnet" would undercharge the opus
    # call the same way.
    record = RunRecord(
        experiment="6",
        arm="6a",
        run=1,
        model="claude-opus-5",  # the run's nominal model — not used for pricing
        calls=(
            Call(model="claude-opus-5", usage=ONE_MILLION_INPUT),
            Call(model="claude-sonnet-5", usage=ONE_MILLION_INPUT),
        ),
    )

    assert record.cost.total == Decimal("5.00") + Decimal("2.00")
