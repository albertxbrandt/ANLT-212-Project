"""Unit tests for inventory rules against a private SQLite database."""

from datetime import date, timedelta
from types import SimpleNamespace

import pytest

from db import connect, init_db
from inventory import (
    InventoryError,
    consume,
    create_location,
    create_product,
    delete_location,
    delete_product,
    insights,
    list_lots,
    move,
    stock,
    update_location,
    waste,
)


TODAY = date(2026, 10, 7)


@pytest.fixture
def conn():
    connection = connect(":memory:")
    init_db(connection, seed=False)
    yield connection
    connection.close()


@pytest.fixture
def kitchen(conn):
    fridge = create_location(conn, "Fridge", "fridge")
    pantry = create_location(conn, "Pantry", "pantry")
    milk = create_product(conn, "Milk", "Dairy", "gal", 10, 2, fridge["id"])
    return SimpleNamespace(conn=conn, fridge=fridge, pantry=pantry, milk=milk)


def test_stock_defaults_expiry_to_shelf_life(kitchen):
    added = TODAY
    lot = stock(kitchen.conn, kitchen.milk["id"], kitchen.fridge["id"], 1, added)
    assert lot["expires_on"] == (added + timedelta(days=10)).isoformat()
    assert lot["status"] == "active"
    assert lot["quantity_remaining"] == 1


def test_names_with_apostrophes_are_stored(conn):
    place = create_location(conn, "O'Brien fridge", "fridge")
    assert place["name"] == "O'Brien fridge"


def test_duplicate_place_is_rejected(kitchen):
    with pytest.raises(InventoryError) as caught:
        create_location(kitchen.conn, "Fridge", "fridge")
    assert caught.value.status == 409


def test_consume_and_waste_finish_a_lot_differently(kitchen):
    used = stock(kitchen.conn, kitchen.milk["id"], kitchen.fridge["id"], 1, TODAY)
    partial = consume(kitchen.conn, used["id"], 0.25, TODAY)
    assert partial["status"] == "active"
    finished = consume(kitchen.conn, used["id"], 0.75, TODAY)
    assert finished["status"] == "depleted"
    assert list_lots(kitchen.conn) == []

    tossed = stock(kitchen.conn, kitchen.milk["id"], kitchen.fridge["id"], 1, TODAY)
    wasted = waste(kitchen.conn, tossed["id"], 1, TODAY, "Sour")
    assert wasted["status"] == "wasted"


def test_cannot_use_more_than_what_is_left(kitchen):
    lot = stock(kitchen.conn, kitchen.milk["id"], kitchen.fridge["id"], 1, TODAY)
    with pytest.raises(InventoryError) as caught:
        consume(kitchen.conn, lot["id"], 2, TODAY)
    assert caught.value.status == 400
    assert list_lots(kitchen.conn)[0]["quantity_remaining"] == 1


def test_finished_lot_cannot_be_used_again(kitchen):
    lot = stock(kitchen.conn, kitchen.milk["id"], kitchen.fridge["id"], 1, TODAY)
    consume(kitchen.conn, lot["id"], 1, TODAY)
    with pytest.raises(InventoryError):
        consume(kitchen.conn, lot["id"], 1, TODAY)


def test_move_records_the_new_place(kitchen):
    lot = stock(kitchen.conn, kitchen.milk["id"], kitchen.fridge["id"], 1, TODAY)
    moved = move(kitchen.conn, lot["id"], kitchen.pantry["id"])
    assert moved["location_id"] == kitchen.pantry["id"]
    with pytest.raises(InventoryError):
        move(kitchen.conn, lot["id"], kitchen.pantry["id"])


def test_expiry_cannot_precede_the_stocked_day(kitchen):
    with pytest.raises(InventoryError):
        stock(
            kitchen.conn,
            kitchen.milk["id"],
            kitchen.fridge["id"],
            1,
            TODAY,
            TODAY - timedelta(days=1),
        )


def test_delete_guards(kitchen):
    spare = create_location(kitchen.conn, "Garage", "other")
    delete_location(kitchen.conn, spare["id"])

    with pytest.raises(InventoryError) as active:
        delete_location(kitchen.conn, kitchen.fridge["id"])
    assert active.value.status == 409

    unused = create_product(kitchen.conn, "Rice", "Pantry", "lb", 365, 1, None)
    delete_product(kitchen.conn, unused["id"])
    stock(kitchen.conn, kitchen.milk["id"], kitchen.fridge["id"], 1, TODAY)
    with pytest.raises(InventoryError) as history:
        delete_product(kitchen.conn, kitchen.milk["id"])
    assert history.value.status == 409


def test_place_with_only_finished_lots_stays_in_the_history(kitchen):
    lot = stock(kitchen.conn, kitchen.milk["id"], kitchen.fridge["id"], 1, TODAY)
    consume(kitchen.conn, lot["id"], 1, TODAY)
    with pytest.raises(InventoryError) as caught:
        delete_location(kitchen.conn, kitchen.fridge["id"])
    assert "history" in str(caught.value)


def test_missing_records_are_not_found(kitchen):
    with pytest.raises(InventoryError) as caught:
        update_location(kitchen.conn, 999, "Cellar", "other")
    assert caught.value.status == 404


def test_replenishment_matches_the_rate_rules(kitchen):
    stock(kitchen.conn, kitchen.milk["id"], kitchen.fridge["id"], 1, TODAY - timedelta(days=1))
    for days_ago in (7,):
        lot = stock(
            kitchen.conn,
            kitchen.milk["id"],
            kitchen.fridge["id"],
            7,
            TODAY - timedelta(days=days_ago),
        )
        consume(kitchen.conn, lot["id"], 7, TODAY - timedelta(days=days_ago))

    report = insights(kitchen.conn, TODAY)
    milk = next(row for row in report["replenishment"] if row["name"] == "Milk")
    assert milk["on_hand"] == 1
    assert milk["daily_rate"] == pytest.approx(7 / 8, abs=0.001)
    assert milk["days_of_cover"] == pytest.approx(1.1, abs=0.1)
    assert milk["suggested_quantity"] == 11.25
    assert milk["restock"] is True
    assert "Below par" in milk["reasons"]
    assert "Less than 7 days of cover" in milk["reasons"]


def test_unknown_rate_still_flags_par(kitchen):
    stock(kitchen.conn, kitchen.milk["id"], kitchen.fridge["id"], 1, TODAY)
    milk = next(row for row in insights(kitchen.conn, TODAY)["replenishment"] if row["name"] == "Milk")
    assert milk["daily_rate"] is None
    assert milk["reasons"] == ["Below par"]
    assert milk["suggested_quantity"] == 1


def test_seed_demo_shows_expiry_shortage_and_waste():
    connection = connect(":memory:")
    init_db(connection, seed=True, today=TODAY)
    init_db(connection, seed=True, today=TODAY)
    report = insights(connection, TODAY)
    assert report["summary"]["expiring_soon"] >= 1
    assert report["summary"]["restock_needed"] >= 1
    assert report["summary"]["waste_events_this_month"] >= 1
    assert len(report["usage_by_week"]) == 8
    assert sum(week["consumed"] for week in report["usage_by_week"]) > 0
    names = [row["product_name"] for row in report["waste_this_month"]]
    assert "Spinach" in names
    connection.close()
