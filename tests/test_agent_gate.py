"""The pass/fail gate, and the rule that keeps prompts out of Python.

The agent itself has no seam: whether it worked is the fixture's exit code, and
asserting past that would mean asserting on model output. The gate that reads
that exit code is a different thing, and it is worth pinning down — a gate that
misreads is the same class of silent corruption as a wrong cost model.
"""

import shutil
from pathlib import Path

from anthropic import Anthropic

from hakka_vibe.agent import FixerAgent

FIXTURE = Path("fixtures/pipeline")


def agent_on(workspace: Path) -> FixerAgent:
    return FixerAgent(
        client=Anthropic(api_key="not-used-by-the-gate"), workspace=workspace, model="claude-opus-5"
    )


def test_the_gate_reports_the_committed_fixture_as_failing(tmp_path: Path) -> None:
    workspace = tmp_path / "pipeline"
    shutil.copytree(FIXTURE, workspace)

    assert agent_on(workspace).check().passed is False


def test_the_gate_reports_a_repaired_fixture_as_passing(tmp_path: Path) -> None:
    # Undo exactly the injected mutation. The gate must notice, or a run that
    # fixed nothing and a run that fixed everything would record identically.
    workspace = tmp_path / "pipeline"
    shutil.copytree(FIXTURE, workspace)
    broken = workspace / "src" / "pipeline" / "stage_2.py"
    broken.write_text(broken.read_text().replace("carried = carried + 2", "carried = carried + 1"))

    assert agent_on(workspace).check().passed is True


def test_no_prompt_text_is_written_into_python() -> None:
    # Prompts live in files so there is one place to change what the model is
    # told. A literal that creeps back into Python drifts away from the version
    # anyone reviewed, and nothing reports it.
    offenders = [
        path
        for path in Path("src").rglob("*.py")
        if "You are " in path.read_text() or "Your task" in path.read_text()
    ]

    assert offenders == []
