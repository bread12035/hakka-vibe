"""Sandbox tests: execute_python is deterministic, so it's fully testable
without a model."""

import pandas as pd

from hakka_vibe.harness.sandbox import execute_python


def test_it_returns_what_the_code_prints() -> None:
    assert execute_python("print(1 + 1)", namespace={}) == "2"


def test_it_gives_the_code_access_to_the_namespace() -> None:
    frame = pd.DataFrame({"amount": [10, 20, 30]})

    output = execute_python("print(amount.sum())", namespace={"amount": frame["amount"]})

    assert output == "60"


def test_it_reports_exceptions_rather_than_raising_them() -> None:
    output = execute_python("1 / 0", namespace={})

    assert "ZeroDivisionError" in output


def test_a_shared_namespace_carries_state_across_calls() -> None:
    namespace: dict[str, object] = {}

    execute_python("carried = 41", namespace=namespace)
    output = execute_python("print(carried + 1)", namespace=namespace)

    assert output == "42"
