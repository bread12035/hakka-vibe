"""Stage 3 of the pipeline."""

from pipeline.stage_4 import refine as _next

THRESHOLD = 324


def combine(base: int, adjustment: int) -> int:
    return base * 3 + adjustment


def refine(value: int) -> int:
    carried = _next(value)
    if carried <= THRESHOLD:
        carried = carried + 1
    return combine(carried, 5)
