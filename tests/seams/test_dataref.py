"""DataRef tests.

ADR-0004: the interface stays thin — preview() and the live object, no query
methods. A query method would restore the per-call round trip pass by
reference exists to remove: the model is meant to write its own code against
the live object instead.
"""

import sqlite3

import pandas as pd

from hakka_vibe.seams.dataref import DataRef


def test_a_dataframes_preview_never_contains_its_row_data() -> None:
    # The test pass by reference exists to satisfy: the full contents of the
    # data must not become characters the model reads, regardless of size.
    frame = pd.DataFrame({"customer_id": range(100_000), "amount": range(100_000)})

    preview = DataRef(name="orders", raw=frame).preview()

    assert "99999" not in preview
    assert len(preview) < 2_000


def test_a_dataframes_preview_names_its_shape_and_columns() -> None:
    frame = pd.DataFrame({"customer_id": [1, 2], "amount": [10.0, 20.0]})

    preview = DataRef(name="orders", raw=frame).preview()

    assert "2" in preview  # row count
    assert "customer_id" in preview
    assert "amount" in preview


def test_a_sqlite_connections_preview_names_its_tables_not_their_rows() -> None:
    connection = sqlite3.connect(":memory:")
    connection.execute("CREATE TABLE orders (customer_id INTEGER, amount REAL)")
    connection.execute("INSERT INTO orders VALUES (424242, 999.99)")

    preview = DataRef(name="orders_db", raw=connection).preview()

    assert "orders" in preview
    assert "424242" not in preview


def test_raw_is_the_same_object_not_a_copy() -> None:
    # This is what "reference" means: the model's code, run in-process, must
    # see the live object, not a serialized stand-in.
    frame = pd.DataFrame({"x": [1]})

    assert DataRef(name="x", raw=frame).raw is frame
