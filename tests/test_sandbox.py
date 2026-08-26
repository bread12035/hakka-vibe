"""Sandbox tests.

execute_python is a deterministic capability: given code and a namespace, it
runs the code and returns what it printed. No model involvement, so it is
fully testable here.
"""

import pandas as pd

from hakka_vibe.sandbox import execute_python


def test_it_returns_what_the_code_prints() -> None:
    assert execute_python("print(1 + 1)", namespace={}) == "2"


def test_it_gives_the_code_access_to_the_namespace() -> None:
    frame = pd.DataFrame({"amount": [10, 20, 30]})

    output = execute_python("print(amount.sum())", namespace={"amount": frame["amount"]})

    assert output == "60"


def test_it_reports_exceptions_rather_than_raising_them() -> None:
    # A raised exception would end the agent's turn with no way to recover; the
    # model needs the error text to try again.
    output = execute_python("1 / 0", namespace={})

    assert "ZeroDivisionError" in output


def test_a_shared_namespace_carries_state_across_calls() -> None:
    # This is the point of the mechanism: a follow-up computation reuses what
    # an earlier turn derived, rather than re-deriving or re-serializing it.
    # See nooa-design/references/patterns.md, "df stays live."
    namespace: dict[str, object] = {}

    execute_python("carried = 41", namespace=namespace)
    output = execute_python("print(carried + 1)", namespace=namespace)

    assert output == "42"
