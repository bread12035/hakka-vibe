"""Cost model: turn token counts into money.

All experiment conclusions are stated in USD rather than token totals, because
the token classes differ in price by up to an order of magnitude and a raw
total silently misrepresents what a change actually saved. See ADR-0002.
"""

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class TokenCounts:
    """Token usage for one call, split by the classes that are priced differently.

    ``thinking`` is a breakdown of ``output``, not a separate class: the API
    reports it inside ``output_tokens``. It is carried so experiments can observe
    reasoning spend, and is deliberately not priced again.
    """

    input: int = 0
    output: int = 0
    thinking: int = 0
    cache_read: int = 0
    cache_write_5m: int = 0
    cache_write_1h: int = 0


@dataclass(frozen=True)
class Cost:
    """A priced breakdown, in USD."""

    input: Decimal
    output: Decimal
    cache_read: Decimal
    cache_write_5m: Decimal
    cache_write_1h: Decimal

    @property
    def total(self) -> Decimal:
        return (
            self.input + self.output + self.cache_read + self.cache_write_5m + self.cache_write_1h
        )


# (input, output) USD per MTok. Cache classes are multipliers on the input price.
_USD_PER_MTOK = {
    "claude-opus-5": (Decimal("5.00"), Decimal("25.00")),
    "claude-sonnet-5": (Decimal("2.00"), Decimal("10.00")),
    "claude-haiku-4-5": (Decimal("1.00"), Decimal("5.00")),
}

_MTOK = Decimal(1_000_000)

# Multipliers on the model's input price, per ADR-0002.
_CACHE_READ_MULTIPLIER = Decimal("0.1")
_CACHE_WRITE_5M_MULTIPLIER = Decimal("1.25")
_CACHE_WRITE_1H_MULTIPLIER = Decimal(2)


def cost_of(tokens: TokenCounts, *, model: str) -> Cost:
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
