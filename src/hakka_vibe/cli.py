"""Command-line entry point: run this project's experiments for real.

The one place a live ``Anthropic()`` client gets built. The SDK already reads
``ANTHROPIC_API_KEY`` and ``ANTHROPIC_BASE_URL`` from the environment on its
own — the latter is how this points at a port-forwarded enterprise endpoint
instead of api.anthropic.com — so the only thing this adds is loading a local
``.env`` (see .env.example) into that environment before the client is built.
"""

import argparse
from pathlib import Path

from anthropic import Anthropic
from dotenv import load_dotenv

from hakka_vibe import report as report_module
from hakka_vibe.experiments.effort_and_workflow import run_effort_and_workflow_experiment
from hakka_vibe.experiments.output_style import run_output_style_experiment
from hakka_vibe.experiments.pass_by_reference import run_pass_by_reference_experiment
from hakka_vibe.experiments.prompt_ordering import run_prompt_ordering_experiment
from hakka_vibe.experiments.subagent_architecture import run_subagent_experiment
from hakka_vibe.experiments.tool_search import run_tool_search_experiment
from hakka_vibe.runner import ArmSummary

DEFAULT_FIXTURE = Path("fixtures/pipeline")
DEFAULT_MODEL = "claude-opus-5"


def run_experiment(
    name: str, *, client: Anthropic, fixture: Path, model: str
) -> dict[str, ArmSummary]:
    """Run one of experiments 1-6 for real, and return its arm summaries.

    Experiment 2's Claude Code arms (2d/2e) are a manual operator procedure,
    not something this harness can drive itself — see
    experiments/pass_by_reference_claude_code.py.
    """
    if name == "1":
        return run_prompt_ordering_experiment(client, fixture=fixture, model=model)
    if name == "2":
        return run_pass_by_reference_experiment(client, model=model)
    if name == "3":
        return run_subagent_experiment(client, fixture=fixture)
    if name == "4":
        return run_tool_search_experiment(client, fixture=fixture, model=model)
    if name == "5":
        return run_output_style_experiment(client, fixture=fixture, model=model)
    if name == "6":
        return run_effort_and_workflow_experiment(client, fixture=fixture, model=model)
    raise ValueError(f"no experiment {name!r}; choose one of 1, 2, 3, 4, 5, 6")


def main() -> None:
    load_dotenv()
    parser = argparse.ArgumentParser(
        description="Run this project's harness token-cost experiments."
    )
    parser.add_argument(
        "experiment",
        choices=["1", "2", "3", "4", "5", "6", "report"],
        help="which experiment to run, or 'report' to regenerate results/REPORT.md",
    )
    parser.add_argument("--fixture", type=Path, default=DEFAULT_FIXTURE)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    args = parser.parse_args()

    if args.experiment == "report":
        report_module.main()
        return

    client = Anthropic()
    summaries = run_experiment(
        args.experiment, client=client, fixture=args.fixture, model=args.model
    )
    for arm, summary in summaries.items():
        print(f"{arm}: median ${summary.median_cost} ({summary.passed}/{summary.runs} passed)")


if __name__ == "__main__":
    main()
