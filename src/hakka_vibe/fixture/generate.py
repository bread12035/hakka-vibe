"""Generate the frozen project an agent is measured against.

Generated rather than taken from a real repository so difficulty is a dial:
every experiment needs eight or more turns of accumulated context to show a
signal, and a fixture that resolves in three turns produces none.

A mutation site is chosen by seeded random selection among sites the generator
itself finds effective — never by a person deciding where a bug would be
interesting to hide, which is a variable the experiments don't want.
"""

import hashlib
import os
import random
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

PIPELINE_INPUT = 7
"""The value the fixture's own test feeds through the pipeline."""


@dataclass(frozen=True)
class MutationSite:
    module: Path
    line: int
    kind: str
    original: str
    mutated: str


@dataclass(frozen=True)
class Fixture:
    """A generated project and the sites a bug can be injected at.

    Sites are held in memory, never written inside the fixture itself — a
    file listing where a bug could be would hand the agent the answer.
    """

    root: Path
    expected: int
    sites: tuple[MutationSite, ...]


def _deepest_stage(constant: int) -> str:
    return f'''"""Base of the pipeline."""


def refine(value: int) -> int:
    return value + {constant}
'''


def _stage(index: int, threshold: int, adjustment: int) -> str:
    return f'''"""Stage {index} of the pipeline."""

from pipeline.stage_{index + 1} import refine as _next

THRESHOLD = {threshold}


def combine(base: int, adjustment: int) -> int:
    return base * 3 + adjustment


def refine(value: int) -> int:
    carried = _next(value)
    if carried <= THRESHOLD:
        carried = carried + 1
    return combine(carried, {adjustment})
'''


def _mutations_for(source: str) -> list[tuple[int, str, str, str]]:
    found = []
    for number, text in enumerate(source.splitlines(), start=1):
        stripped = text.strip()
        if stripped.startswith("if carried <="):
            found.append((number, "comparison", text, text.replace("<=", "<")))
        elif stripped.startswith("carried = carried +"):
            found.append((number, "off_by_one", text, text.replace("+ 1", "+ 2")))
        elif stripped.startswith("return combine("):
            inner = stripped[len("return combine(") : -1]
            first, second = (part.strip() for part in inner.split(","))
            found.append(
                (number, "argument_order", text, text.replace(inner, f"{second}, {first}"))
            )
    return found


def _stage_result(root: Path, index: int) -> int:
    """Run the generated pipeline and return what it computes.

    Bytecode caching is off: Python invalidates a .pyc on size and mtime, and
    two of the mutations below leave the file the same size, so a probe run
    inside the same mtime tick could silently execute the previous version.
    """
    completed = subprocess.run(
        [
            sys.executable,
            "-B",
            "-c",
            (
                "import sys; sys.path.insert(0, 'src'); "
                f"from pipeline.stage_{index} import refine; "
                f"print(refine({PIPELINE_INPUT}))"
            ),
        ],
        cwd=root,
        capture_output=True,
        text=True,
        check=True,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
    )
    return int(completed.stdout.strip())


def _pipeline_result(root: Path) -> int:
    return _stage_result(root, 0)


def _rewrite_line(path: Path, line: int, text: str) -> None:
    lines = path.read_text().splitlines(keepends=True)
    ending = "\n" if lines[line - 1].endswith("\n") else ""
    lines[line - 1] = text + ending
    path.write_text("".join(lines))


def generate_fixture(root: Path, *, depth: int, seed: int) -> Fixture:
    """Write a working ``depth``-stage project, and report where it can break.

    Only sites that actually change the pipeline's output are reported — a
    mutation that leaves the result unchanged would inject a bug the fixture's
    own test can't see, and a run would pass while measuring nothing.
    """
    if depth < 2:
        raise ValueError("depth must be at least 2 so the bug can sit below the test")

    rng = random.Random(seed)
    package = root / "src" / "pipeline"
    package.mkdir(parents=True, exist_ok=True)
    (package / "__init__.py").write_text('"""A small staged pipeline."""\n')

    for index in range(depth - 1):
        (package / f"stage_{index}.py").write_text(
            _stage(index, threshold=0, adjustment=rng.randrange(1, 9))
        )
    (package / f"stage_{depth - 1}.py").write_text(_deepest_stage(rng.randrange(1, 9)))

    # pytest.ini rather than pyproject.toml: a pyproject.toml with no
    # [project] table is valid for pytest but reads as a broken package to
    # other Python tooling — friction the agent under test shouldn't meet.
    (root / "pytest.ini").write_text("[pytest]\npythonpath = src\n")

    # Each threshold is set to the value that actually reaches it, so the
    # comparison sits exactly on its boundary. Left at a random constant the
    # boundary is never touched, and <= -> < changes nothing.
    for index in range(depth - 2, -1, -1):
        module = package / f"stage_{index}.py"
        carried = _stage_result(root, index + 1)
        for number, text in enumerate(module.read_text().splitlines(), start=1):
            if text.startswith("THRESHOLD ="):
                _rewrite_line(module, number, f"THRESHOLD = {carried}")
                break

    expected = _pipeline_result(root)

    tests = root / "tests"
    tests.mkdir(exist_ok=True)
    (tests / "test_pipeline.py").write_text(
        f'''"""The pipeline produces the value it is contracted to produce."""

from pipeline.stage_0 import refine


def test_pipeline_refines_to_its_known_result() -> None:
    assert refine({PIPELINE_INPUT}) == {expected}
'''
    )

    sites = []
    # Stage 0 excluded: the bug must sit below the module the test imports, so
    # finding it means reading past the first file.
    for index in range(1, depth - 1):
        module = package / f"stage_{index}.py"
        source = module.read_text()
        for line, kind, original, mutated in _mutations_for(source):
            _rewrite_line(module, line, mutated)
            changed = _pipeline_result(root) != expected
            _rewrite_line(module, line, original)
            if changed:
                sites.append(
                    MutationSite(
                        module=module.relative_to(root),
                        line=line,
                        kind=kind,
                        original=original,
                        mutated=mutated,
                    )
                )

    return Fixture(root=root, expected=expected, sites=tuple(sites))


def inject_bug(fixture: Fixture, *, seed: int) -> MutationSite:
    """Apply one randomly-chosen mutation and report which one it was."""
    if not fixture.sites:
        raise ValueError("fixture has no effective mutation sites")
    site = random.Random(seed).choice(fixture.sites)
    _rewrite_line(fixture.root / site.module, site.line, site.mutated)
    return site


def fixture_fingerprint(root: Path) -> str:
    """Identify which version of a fixture a run was measured on.

    A verdict only means something against the exact fixture it was measured
    on; when a fixture is deepened and regenerated the fingerprint changes,
    so an old calibration can't silently appear to still apply.
    """
    digest = hashlib.sha256()
    for path in sorted(root.rglob("*.py")):
        digest.update(str(path.relative_to(root)).encode())
        digest.update(path.read_bytes())
    return digest.hexdigest()[:16]
