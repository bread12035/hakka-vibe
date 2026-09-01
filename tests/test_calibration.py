"""Calibration gate tests: a pure function over a run record, fully testable
without spending a call."""

from pathlib import Path

from hakka_vibe.fixture.calibration import MINIMUM_TURNS, calibrate
from hakka_vibe.fixture.generate import fixture_fingerprint, generate_fixture
from hakka_vibe.measurement.run_record import Call, RunRecord, read_run_record, write_run_record

USAGE = {
    "input_tokens": 10,
    "output_tokens": 20,
    "output_tokens_details": None,
    "cache_read_input_tokens": 0,
    "cache_creation": None,
}


def record_of(turns: int) -> RunRecord:
    return RunRecord(
        experiment="6",
        arm="6a",
        run=1,
        model="claude-opus-5",
        calls=tuple(Call(model="claude-opus-5", usage=USAGE) for _ in range(turns)),
        passed=True,
    )


def test_a_fixture_resolved_too_quickly_is_rejected() -> None:
    verdict = calibrate(record_of(3))

    assert verdict.accepted is False
    assert verdict.turns == 3
    assert verdict.minimum == MINIMUM_TURNS


def test_a_fixture_that_takes_enough_turns_is_accepted() -> None:
    assert calibrate(record_of(MINIMUM_TURNS)).accepted is True


def test_the_boundary_is_inclusive() -> None:
    assert calibrate(record_of(MINIMUM_TURNS - 1)).accepted is False
    assert calibrate(record_of(MINIMUM_TURNS)).accepted is True


def test_a_fingerprint_identifies_which_fixture_a_run_used(tmp_path: Path) -> None:
    original = generate_fixture(tmp_path / "a", depth=4, seed=1)
    identical = generate_fixture(tmp_path / "b", depth=4, seed=1)
    deepened = generate_fixture(tmp_path / "c", depth=6, seed=1)

    assert fixture_fingerprint(original.root) == fixture_fingerprint(identical.root)
    assert fixture_fingerprint(original.root) != fixture_fingerprint(deepened.root)


def test_a_run_record_carries_which_fixture_it_was_measured_on(tmp_path: Path) -> None:
    fixture = generate_fixture(tmp_path / "f", depth=4, seed=1)
    record = RunRecord(
        experiment="6",
        arm="6a",
        run=1,
        model="claude-opus-5",
        calls=(Call(model="claude-opus-5", usage=USAGE),),
        fixture=fixture_fingerprint(fixture.root),
    )

    stored = write_run_record(record, root=tmp_path / "results")

    assert read_run_record(stored).fixture == fixture_fingerprint(fixture.root)
