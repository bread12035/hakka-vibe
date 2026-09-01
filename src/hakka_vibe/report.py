"""The summary report over whatever run records currently exist in results/.

Never raises on missing or partial data: real experiments complete arms one
at a time, not all at once, so an arm with fewer than three runs is reported
as incomplete rather than crashing the whole report.
"""

import json
from pathlib import Path

from hakka_vibe.measurement.run_record import DEFAULT_RESULTS_ROOT, Call, RunRecord
from hakka_vibe.runner import RUNS_PER_ARM, ArmSummary, summarise

CLAUDE_CODE_ARMS = {"2d", "2e"}
"""Arms executed under Claude Code rather than the self-built harness. Their
cache writes are fixed at the 1 hour TTL — Claude Code's own behaviour, not a
setting this project controls — so their percentages never belong in the same
table as the self-built harness's 5-minute-TTL results."""

KNOWN_LIMITATIONS = """\
## Known limitations

- The fixture is synthetic. Relative differences between arms are
  trustworthy; absolute dollar figures do not transfer to real projects.
- The fixture-generating model and the model under measurement are in the
  same family, a validity threat the mechanically-injected bug reduces but
  does not remove.
- Self-built-harness results (5 minute cache TTL) and Claude Code results
  (fixed 1 hour TTL) are priced on different bases and are not comparable to
  each other, even for the same nominal experiment.
"""


def _load_arm(root: Path, experiment: str, arm: str) -> list[RunRecord]:
    directory = root / experiment / arm
    if not directory.is_dir():
        return []
    records = []
    for path in sorted(directory.glob("*.json")):
        stored = json.loads(path.read_text())
        records.append(
            RunRecord(
                experiment=stored["experiment"],
                arm=stored["arm"],
                run=stored["run"],
                model=stored["model"],
                calls=tuple(Call(model=c["model"], usage=c["usage"]) for c in stored["calls"]),
                passed=stored["passed"],
                fixture=stored.get("fixture"),
            )
        )
    return records


def _found_arms(root: Path) -> list[tuple[str, str]]:
    if not root.is_dir():
        return []
    found = []
    for experiment_dir in sorted(root.iterdir()):
        if not experiment_dir.is_dir():
            continue
        for arm_dir in sorted(experiment_dir.iterdir()):
            if arm_dir.is_dir():
                found.append((experiment_dir.name, arm_dir.name))
    return found


def _arm_section(experiment: str, arm: str, records: list[RunRecord]) -> str:
    if len(records) != RUNS_PER_ARM:
        return f"- **{experiment}/{arm}**: incomplete ({len(records)}/{RUNS_PER_ARM} runs)"

    summary: ArmSummary = summarise(arm, records)
    label = (
        " (Claude Code — not comparable to self-built-harness arms)"
        if arm in CLAUDE_CODE_ARMS
        else ""
    )
    return (
        f"- **{experiment}/{arm}**{label}: median ${summary.median_cost} "
        f"(range ${summary.lowest_cost}-${summary.highest_cost}), "
        f"{summary.passed}/{summary.runs} passed"
    )


def build_report(results_root: Path) -> str:
    """Render whatever is under ``results_root`` into a Markdown summary."""
    arms = _found_arms(results_root)
    lines = ["# Harness token cost experiments — summary report", ""]

    if not arms:
        lines.append(
            "No run data exists yet. Every experiment is still in-progress "
            "pending real API calls against the synthetic fixture."
        )
    else:
        lines.append("## Arms")
        lines.append("")
        for experiment, arm in arms:
            lines.append(_arm_section(experiment, arm, _load_arm(results_root, experiment, arm)))

    lines.extend(["", KNOWN_LIMITATIONS])
    return "\n".join(lines)


def main() -> None:
    """Regenerate results/REPORT.md from whatever is currently in results/."""
    report = build_report(DEFAULT_RESULTS_ROOT)
    (DEFAULT_RESULTS_ROOT / "REPORT.md").write_text(report)


if __name__ == "__main__":
    main()
