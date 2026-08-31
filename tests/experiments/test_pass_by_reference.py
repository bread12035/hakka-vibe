"""Analysis task tests: the dataset, its question, and its independently-known answer.

The expected answer is computed by a different method than the one under test,
so a wrong analysis cannot pass by accident (tdd's tautology anti-pattern).
"""

from hakka_vibe.experiments.pass_by_reference import generate_orders, top_customer_by_total


def test_the_generator_is_reproducible_for_a_given_seed() -> None:
    # Runs of one arm are spread over days; a dataset that drifts between them
    # makes the runs incomparable.
    first = generate_orders(rows=1_000, seed=7)
    second = generate_orders(rows=1_000, seed=7)

    assert first.equals(second)


def test_the_known_answer_is_computed_independently_of_pandas() -> None:
    # A plain-Python loop over the same rows, so the fixture's answer key does
    # not depend on the library the agent is being measured using.
    orders = generate_orders(rows=500, seed=1)

    expected = top_customer_by_total(orders)

    totals: dict[int, float] = {}
    for _, row in orders.iterrows():
        totals[row["customer_id"]] = totals.get(row["customer_id"], 0.0) + row["amount"]
    independently_computed = max(totals.items(), key=lambda pair: pair[1])

    assert (expected.customer_id, round(expected.total, 2)) == (
        independently_computed[0],
        round(independently_computed[1], 2),
    )


def test_a_well_formed_answer_line_is_parsed() -> None:
    from hakka_vibe.experiments.pass_by_reference import parse_answer

    parsed = parse_answer("I looked at the data.\n\nANSWER: 42 1234.56\n")

    assert parsed is not None
    assert parsed.customer_id == 42
    assert parsed.total == 1234.56


def test_a_missing_answer_line_parses_to_none() -> None:
    from hakka_vibe.experiments.pass_by_reference import parse_answer

    assert parse_answer("I ran out of turns before finishing.") is None


def test_the_gate_accepts_a_small_rounding_difference() -> None:
    from hakka_vibe.experiments.pass_by_reference import TopCustomer, matches_expected

    expected = TopCustomer(customer_id=42, total=1234.56)

    assert matches_expected(TopCustomer(customer_id=42, total=1234.555), expected)
    assert not matches_expected(TopCustomer(customer_id=42, total=1235.00), expected)
    assert not matches_expected(TopCustomer(customer_id=7, total=1234.56), expected)


def test_arm_2a_puts_the_whole_dataset_in_the_task_context() -> None:
    from hakka_vibe.experiments.pass_by_reference import build_arms

    orders = generate_orders(rows=200, seed=3)
    arms = build_arms(orders)

    assert arms["2a"].data is None
    # Every row's amount is a substring of the pasted CSV: nothing is hidden or
    # summarised, the full contents became prompt characters.
    for amount in orders["amount"]:
        assert str(amount) in arms["2a"].task_context


def test_arms_2b_and_2c_carry_a_live_reference_not_the_rows() -> None:
    from hakka_vibe.experiments.pass_by_reference import build_arms

    orders = generate_orders(rows=200, seed=3)
    arms = build_arms(orders)

    assert arms["2b"].data is not None and arms["2b"].data.name == "orders"
    assert arms["2c"].data is not None and arms["2c"].data.name == "orders_db"
    # The context text names the variable; it never contains a row's amount.
    for amount in orders["amount"].head(5):
        assert str(amount) not in arms["2b"].task_context
        assert str(amount) not in arms["2c"].task_context
