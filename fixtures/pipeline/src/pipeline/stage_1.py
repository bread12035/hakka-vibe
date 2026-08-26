"""Stage 1 of the pipeline."""

from pipeline.stage_2 import refine as _next

THRESHOLD = 2945


def combine(base: int, adjustment: int) -> int:
    return base * 3 + adjustment


def refine(value: int) -> int:
    carried = _next(value)
    if carried <= THRESHOLD:
        carried = carried + 1
    return combine(carried, 1)
