from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from sqlalchemy import create_engine, text

from queries.select_queries import select_with_filter, supabase_select_paginated
from queries.write_queries import delete_rows, update_rows


@pytest.fixture
def engine():
    db = create_engine("sqlite://")
    with db.begin() as connection:
        connection.execute(
            text(
                "CREATE TABLE items (id INTEGER PRIMARY KEY, category TEXT, title TEXT)"
            )
        )
        connection.execute(
            text(
                "INSERT INTO items VALUES (1, NULL, 'first'), (2, 'known', 'second'), (3, NULL, 'third')"
            )
        )
    yield db
    db.dispose()


def test_nullable_select_update_and_delete_target_only_null_rows(engine):
    assert [
        row["id"] for row in select_with_filter(engine, "items", "category", None)
    ] == [1, 3]
    assert update_rows(engine, "items", {"title": "review"}, "category", None) == 2
    assert (
        select_with_filter(engine, "items", "category", "known")[0]["title"] == "second"
    )
    assert delete_rows(engine, "items", "category", None) == 2
    assert select_with_filter(engine, "items", "id", 2)[0]["category"] == "known"


def test_nullable_updates_still_bind_values_and_quote_column_names(engine):
    value = "value'; DELETE FROM items; --"
    assert update_rows(engine, "items", {"category": value}, "category", None) == 2
    assert len(select_with_filter(engine, "items", "category", value)) == 2
    with pytest.raises(ValueError):
        delete_rows(engine, "items", "category OR 1=1", None)
    assert len(select_with_filter(engine, "items", "category", "known")) == 1


def test_supabase_pages_have_an_explicit_stable_order():
    client = Mock()
    query = client.table.return_value.select.return_value
    query.order.return_value.range.return_value.execute.return_value = SimpleNamespace(
        data=[{"id": 6}]
    )
    assert supabase_select_paginated(client, "items", page=2, page_size=5) == [
        {"id": 6}
    ]
    query.order.assert_called_once_with("id")
    query.order.return_value.range.assert_called_once_with(5, 9)


@pytest.mark.parametrize("key", ["id,secret", "id.desc", "id; DROP TABLE items", None])
def test_invalid_page_order_does_not_contact_supabase(key):
    client = Mock()
    with pytest.raises(ValueError):
        supabase_select_paginated(client, "items", order_by=key)
    client.table.assert_not_called()
