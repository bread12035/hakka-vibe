"""Cost model tests.

Expected values are hand-computed from the published per-MTok prices, never
recomputed the way the implementation does it.
"""

from decimal import Decimal

from hakka_vibe.measurement.cost import TokenCounts, cost_of


def test_input_tokens_are_charged_at_the_model_list_price() -> None:
    # Claude Opus 5 input is $5.00 per MTok. 200,000 tokens = 0.2 MTok.
    tokens = TokenCounts(input=200_000)

    assert cost_of(tokens, model="claude-opus-5").total == Decimal("1.00")


def test_cache_read_is_charged_at_a_tenth_of_the_input_price() -> None:
    # Cache read on Opus 5 is 0.1 * $5.00 = $0.50/MTok.
    tokens = TokenCounts(input=2, cache_read=222_908)

    assert cost_of(tokens, model="claude-opus-5").total == Decimal("0.111464")


def test_cache_write_is_priced_by_ttl() -> None:
    # 5m write is 1.25x input price, 1h write is 2x — the same tokens must
    # never collapse into one blended "cache write" figure.
    written = 10_319

    five_minute = cost_of(TokenCounts(cache_write_5m=written), model="claude-opus-5")
    one_hour = cost_of(TokenCounts(cache_write_1h=written), model="claude-opus-5")

    assert five_minute.total == Decimal("0.06449375")
    assert one_hour.total == Decimal("0.10319")


def test_thinking_tokens_are_a_breakdown_of_output_not_an_addition() -> None:
    # The API reports thinking nested inside output_tokens; pricing it again
    # would inflate every reasoning-heavy arm.
    with_thinking = TokenCounts(output=971, thinking=580)
    same_output_no_thinking = TokenCounts(output=971, thinking=0)

    assert cost_of(with_thinking, model="claude-opus-5").total == Decimal("0.024275")
    assert (
        cost_of(with_thinking, model="claude-opus-5").total
        == cost_of(same_output_no_thinking, model="claude-opus-5").total
    )


def test_each_model_is_priced_at_its_own_rate() -> None:
    # Experiment 3 runs a subagent on a cheaper model; the same tokens must not
    # be priced as if everything ran on the frontier model.
    one_mtok = TokenCounts(input=1_000_000)

    assert cost_of(one_mtok, model="claude-opus-5").total == Decimal("5.00")
    assert cost_of(one_mtok, model="claude-sonnet-5").total == Decimal("2.00")
