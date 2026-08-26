"""The pipeline produces the value it is contracted to produce."""

from pipeline.stage_0 import refine


def test_pipeline_refines_to_its_known_result() -> None:
    assert refine(7) == 26528
