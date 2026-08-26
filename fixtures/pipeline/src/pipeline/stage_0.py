"""Stage 0 of the pipeline."""

from pipeline.stage_1 import refine as _next

THRESHOLD = 8839


def combine(base: int, adjustment: int) -> int:
    return base * 3 + adjustment


def refine(value: int) -> int:
    carried = _next(value)
    if carried <= THRESHOLD:
        carried = carried + 1
    return combine(carried, 8)
