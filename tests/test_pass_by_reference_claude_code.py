"""Experiment 2d-2e materials and grading (Claude Code).

Driving an actual Claude Code session is a human/operator step this harness
cannot invoke from inside itself: it would mean this session spawning another
copy of itself. What is built and tested here is everything up to and after
that step — the materials each arm's session starts from, and grading the
transcript it produces.
"""

from pathlib import Path

from hakka_vibe.experiments.pass_by_reference_claude_code import write_materials


def test_arm_2e_prompt_contains_the_whole_dataset_as_text(tmp_path: Path) -> None:
    materials = write_materials(tmp_path, rows=200, seed=5)

    for amount in materials.orders["amount"]:
        assert str(amount) in materials.prompt_2e


def test_arm_2d_prompt_points_at_a_file_rather_than_pasting_rows(tmp_path: Path) -> None:
    materials = write_materials(tmp_path, rows=200, seed=5)

    assert materials.csv_path.name in materials.prompt_2d
    for amount in materials.orders["amount"].head(5):
        assert str(amount) not in materials.prompt_2d


def test_the_csv_file_is_written_to_disk_for_2d_to_read(tmp_path: Path) -> None:
    materials = write_materials(tmp_path, rows=50, seed=1)

    assert materials.csv_path.is_file()
    assert "customer_id" in materials.csv_path.read_text()


def test_grading_a_transcript_that_answers_correctly_marks_the_run_passed(tmp_path: Path) -> None:
    import json

    from hakka_vibe.experiments.pass_by_reference import TopCustomer
    from hakka_vibe.experiments.pass_by_reference_claude_code import grade_transcript

    expected = TopCustomer(customer_id=7, total=999.99)
    transcript = tmp_path / "session.jsonl"
    transcript.write_text(
        json.dumps(
            {
                "type": "assistant",
                "message": {
                    "model": "claude-opus-5",
                    "content": [{"type": "text", "text": "ANSWER: 7 999.99"}],
                    "usage": {
                        "input_tokens": 10,
                        "output_tokens": 10,
                        "output_tokens_details": None,
                        "cache_read_input_tokens": 0,
                        "cache_creation": None,
                    },
                },
            }
        )
    )

    record = grade_transcript(transcript, expected=expected, arm="2d", run=1)

    assert record.passed is True
    assert record.arm == "2d"


def test_grading_a_transcript_with_the_wrong_answer_marks_the_run_failed(tmp_path: Path) -> None:
    import json

    from hakka_vibe.experiments.pass_by_reference import TopCustomer
    from hakka_vibe.experiments.pass_by_reference_claude_code import grade_transcript

    expected = TopCustomer(customer_id=7, total=999.99)
    transcript = tmp_path / "session.jsonl"
    transcript.write_text(
        json.dumps(
            {
                "type": "assistant",
                "message": {
                    "model": "claude-opus-5",
                    "content": [{"type": "text", "text": "ANSWER: 3 1.00"}],
                    "usage": {
                        "input_tokens": 10,
                        "output_tokens": 10,
                        "output_tokens_details": None,
                        "cache_read_input_tokens": 0,
                        "cache_creation": None,
                    },
                },
            }
        )
    )

    record = grade_transcript(transcript, expected=expected, arm="2d", run=1)

    assert record.passed is False
