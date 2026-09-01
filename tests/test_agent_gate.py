"""The pass/fail gate, and the rule that keeps prompts out of Python.

The fixer has no seam of its own: whether it worked is the fixture's exit
code, and asserting past that would mean asserting on model output. The gate
that reads that exit code is a different thing, worth pinning down on its
own — a gate that misreads is the same class of silent corruption as a wrong
cost model.
"""

import shutil
from pathlib import Path

from hakka_vibe.agents import fixer

FIXTURE = Path("fixtures/pipeline")


def test_the_gate_reports_the_committed_fixture_as_failing(tmp_path: Path) -> None:
    workspace = tmp_path / "pipeline"
    shutil.copytree(FIXTURE, workspace)

    assert fixer.check(workspace).passed is False


def test_the_gate_reports_a_repaired_fixture_as_passing(tmp_path: Path) -> None:
    # Undo exactly the injected mutation. The gate must notice, or a run that
    # fixed nothing and a run that fixed everything would record identically.
    workspace = tmp_path / "pipeline"
    shutil.copytree(FIXTURE, workspace)
    broken = workspace / "src" / "pipeline" / "stage_2.py"
    broken.write_text(broken.read_text().replace("carried = carried + 2", "carried = carried + 1"))

    assert fixer.check(workspace).passed is True


def test_no_prompt_text_is_written_into_python() -> None:
    offenders = [
        path
        for path in Path("src").rglob("*.py")
        if "You are " in path.read_text() or "Your task" in path.read_text()
    ]

    assert offenders == []
