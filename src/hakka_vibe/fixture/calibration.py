"""The gate that decides whether a fixture is hard enough to measure on.

A fixture a baseline resolves in a handful of turns leaves no accumulated
context — and every experiment that depends on that accumulation (cache
behaviour, subagent context passing, reasoning spend) would read the same on
every arm. Difficulty is a dial, not a guess: this is what makes it a
verified dial rather than an assumed one.
"""

from dataclasses import dataclass

from hakka_vibe.measurement.run_record import RunRecord

MINIMUM_TURNS = 8
"""Fewer turns than this and the fixture is rejected rather than used."""


@dataclass(frozen=True)
class Calibration:
    turns: int
    minimum: int
    accepted: bool

    @property
    def remedy(self) -> str:
        if self.accepted:
            return "fixture accepted"
        return (
            f"fixture resolved in {self.turns} turns, under the {self.minimum} required: "
            "deepen it and regenerate rather than using it as is"
        )


def calibrate(baseline: RunRecord) -> Calibration:
    """Judge a fixture from one baseline run — a turn is a call, so nothing
    beyond the record itself is needed."""
    turns = len(baseline.calls)
    return Calibration(turns=turns, minimum=MINIMUM_TURNS, accepted=turns >= MINIMUM_TURNS)
