"""Fixture generator tests. The seam is the generated fixture itself, observed
by running its own pytest.
"""

import subprocess
import sys
from pathlib import Path

from hakka_vibe.fixture.generate import generate_fixture, inject_bug


def run_fixture_tests(root: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "pytest", "-q"],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )


def test_a_freshly_generated_fixture_passes_its_own_tests(tmp_path: Path) -> None:
    generate_fixture(tmp_path, depth=4, seed=1)

    assert run_fixture_tests(tmp_path).returncode == 0


def test_an_injected_bug_turns_the_fixture_red(tmp_path: Path) -> None:
    fixture = generate_fixture(tmp_path, depth=4, seed=1)

    inject_bug(fixture, seed=1)

    assert run_fixture_tests(tmp_path).returncode != 0


def test_the_bug_sits_in_a_different_module_from_the_failing_test(tmp_path: Path) -> None:
    fixture = generate_fixture(tmp_path, depth=4, seed=1)

    site = inject_bug(fixture, seed=1)
    failure = run_fixture_tests(tmp_path).stdout

    assert "tests/test_pipeline.py" in failure
    assert site.module != Path("tests/test_pipeline.py")
    assert site.module != Path("src/pipeline/stage_0.py")


def test_every_mutation_kind_is_available_to_be_chosen(tmp_path: Path) -> None:
    fixture = generate_fixture(tmp_path, depth=4, seed=1)

    assert {site.kind for site in fixture.sites} == {
        "comparison",
        "off_by_one",
        "argument_order",
    }


def test_depth_controls_how_far_the_cause_can_sit_from_the_test(tmp_path: Path) -> None:
    shallow = generate_fixture(tmp_path / "shallow", depth=3, seed=1)
    deep = generate_fixture(tmp_path / "deep", depth=7, seed=1)

    assert len(deep.sites) > len(shallow.sites)
    assert run_fixture_tests(tmp_path / "deep").returncode == 0


def test_the_same_seed_regenerates_the_same_fixture(tmp_path: Path) -> None:
    first = generate_fixture(tmp_path / "first", depth=4, seed=99)
    second = generate_fixture(tmp_path / "second", depth=4, seed=99)

    assert first.expected == second.expected
    assert [(s.module, s.line, s.kind) for s in first.sites] == [
        (s.module, s.line, s.kind) for s in second.sites
    ]
