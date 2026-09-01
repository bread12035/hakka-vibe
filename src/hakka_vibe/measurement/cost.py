"""Cost model: price token counts in USD.

Every experiment's conclusion is stated in dollars, not raw token totals — the
token classes span an order of magnitude in price, so a raw sum silently
misrepresents what a change actually saved.
"""

from dataclasses import dataclass
from decimal import Decimal

_MTOK = Decimal(1_000_000)

# USD per million tokens, (input, output). Cache classes are multipliers on
# the model's own input price, not separate absolute prices.
_USD_PER_MTOK: dict[str, tuple[Decimal, Decimal]] = {
    "claude-opus-5": (Decimal("5.00"), Decimal("25.00")),
    "claude-sonnet-5": (Decimal("2.00"), Decimal("10.00")),
    "claude-haiku-4-5": (Decimal("1.00"), Decimal("5.00")),
}

_CACHE_READ_MULTIPLIER = Decimal("0.1")
_CACHE_WRITE_5M_MULTIPLIER = Decimal("1.25")
_CACHE_WRITE_1H_MULTIPLIER = Decimal(2)


@dataclass(frozen=True)
class TokenCounts:
    """One call's usage, split by the classes the cost model prices differently.

    ``thinking`` is a breakdown of ``output`` (the API reports it nested
    inside output_tokens), carried for visibility and never priced twice.
    """

    input: int = 0
    output: int = 0
    thinking: int = 0
    cache_read: int = 0
    cache_write_5m: int = 0
    cache_write_1h: int = 0

    def __add__(self, other: "TokenCounts") -> "TokenCounts":
        return TokenCounts(
            input=self.input + other.input,
            output=self.output + other.output,
            thinking=self.thinking + other.thinking,
            cache_read=self.cache_read + other.cache_read,
            cache_write_5m=self.cache_write_5m + other.cache_write_5m,
            cache_write_1h=self.cache_write_1h + other.cache_write_1h,
        )


@dataclass(frozen=True)
class Cost:
    """A priced breakdown, in USD, by the same classes as ``TokenCounts``."""

    input: Decimal
    output: Decimal
    cache_read: Decimal
    cache_write_5m: Decimal
    cache_write_1h: Decimal

    def __add__(self, other: "Cost") -> "Cost":
        return Cost(
            input=self.input + other.input,
            output=self.output + other.output,
            cache_read=self.cache_read + other.cache_read,
            cache_write_5m=self.cache_write_5m + other.cache_write_5m,
            cache_write_1h=self.cache_write_1h + other.cache_write_1h,
        )

    @property
    def total(self) -> Decimal:
        return (
            self.input + self.output + self.cache_read + self.cache_write_5m + self.cache_write_1h
        )


ZERO_COST = Cost(
    input=Decimal(0),
    output=Decimal(0),
    cache_read=Decimal(0),
    cache_write_5m=Decimal(0),
    cache_write_1h=Decimal(0),
)


def cost_of(tokens: TokenCounts, *, model: str) -> Cost:
    """Price one call's token counts at ``model``'s own rate card."""
    input_price, output_price = _USD_PER_MTOK[model]

    def priced(count: int, multiplier: Decimal = Decimal(1)) -> Decimal:
        return Decimal(count) / _MTOK * input_price * multiplier

    return Cost(
        input=priced(tokens.input),
        output=Decimal(tokens.output) / _MTOK * output_price,
        cache_read=priced(tokens.cache_read, _CACHE_READ_MULTIPLIER),
        cache_write_5m=priced(tokens.cache_write_5m, _CACHE_WRITE_5M_MULTIPLIER),
        cache_write_1h=priced(tokens.cache_write_1h, _CACHE_WRITE_1H_MULTIPLIER),
    )
