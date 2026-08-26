"""Summary report tests.

No real run data exists yet — every arm is still in-progress pending
credentials. What's testable is the report generator itself: given whatever
run records are on disk, does it group, price, and label them correctly. The
tests write synthetic records via write_run_record and read the report back.
"""

from pathlib import Path

from hakka_vibe.report import build_report
from hakka_vibe.run_record import Call, RunRecord, write_run_record

USAGE = {
    "input_tokens": 100,
    "output_tokens": 200,
    "output_tokens_details": None,
    "cache_read_input_tokens": 0,
    "cache_creation": None,
}


def write_complete_arm(
    root: Path, *, experiment: str, arm: str, model: str = "claude-opus-5"
) -> None:
    for run in range(1, 4):
        record = RunRecord(
            experiment=experiment,
            arm=arm,
            run=run,
            model=model,
            calls=(Call(model=model, usage=USAGE),),
            passed=True,
        )
        write_run_record(record, root=root)


def test_a_complete_arm_reports_its_median_in_usd(tmp_path: Path) -> None:
    write_complete_arm(tmp_path, experiment="6", arm="6a")

    report = build_report(tmp_path)

    # 100 input @ $5/MTok + 200 output @ $25/MTok = $0.0005 + $0.005 = $0.0055
    assert "$0.0055" in report
    assert "6a" in report


def test_an_incomplete_arm_is_reported_as_incomplete_not_crashed(tmp_path: Path) -> None:
    record = RunRecord(
        experiment="6",
        arm="6b",
        run=1,
        model="claude-opus-5",
        calls=(Call(model="claude-opus-5", usage=USAGE),),
    )
    write_run_record(record, root=tmp_path)

    report = build_report(tmp_path)

    assert "6b" in report
    assert "incomplete" in report.lower() or "1/3" in report


def test_claude_code_arms_are_labelled_separately_from_the_self_built_harness(
    tmp_path: Path,
) -> None:
    write_complete_arm(tmp_path, experiment="2", arm="2a")
    write_complete_arm(tmp_path, experiment="2", arm="2d")

    report = build_report(tmp_path)

    # 2d/2e write cache at Claude Code's fixed 1-hour TTL; 2a-2c are the
    # self-built harness's 5-minute-TTL results. Different pricing basis, so
    # they must never appear in one comparable table.
    assert "not comparable" in report.lower() or "不可跨比" in report


def test_an_empty_results_directory_still_produces_a_report(tmp_path: Path) -> None:
    # The report is the deliverable even before any run has executed: it
    # should state its own known limitations regardless of what data exists.
    report = build_report(tmp_path)

    assert "synthetic" in report.lower() or "合成" in report


def test_the_known_limitations_are_always_present(tmp_path: Path) -> None:
    write_complete_arm(tmp_path, experiment="6", arm="6a")

    report = build_report(tmp_path)

    assert "do not transfer" in report.lower() or "不可外推" in report
