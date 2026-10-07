"""Household inventory rules.

Locations, products, lots, and the event log are changed only through these
functions. Prediction uses the event log and is not stored. This module does
not import Flask.
"""

import math
import os
import sqlite3
from datetime import date, datetime, timedelta


KINDS = ("fridge", "freezer", "pantry", "other")
RESTOCK_DAYS = 7
COVER_TARGET_DAYS = 14
RATE_WINDOW_DAYS = 28
USAGE_WEEKS = 8


class InventoryError(Exception):
    """A rule the caller can show to the user.

    status is an HTTP code the route layer can return unchanged.
    """

    def __init__(self, message, status=400):
        super().__init__(message)
        self.status = status


def current_day():
    """Return the household's current date.

    INVENTORY_TODAY=YYYY-MM-DD overrides the clock so a demo or test can pin
    "today" without changing the machine date.
    """
    raw = os.getenv("INVENTORY_TODAY")
    if raw:
        return date.fromisoformat(raw)
    return date.today()


def consumption_rate(quantities_by_day, today):
    """Daily use rate from consumed quantities keyed by date.

    The window starts 28 days before today and runs through today. The divisor
    is the inclusive day count from the first consumption in that window
    through today. Returns None when the window has no consumption.

    Args:
        quantities_by_day: Mapping of datetime.date to quantity consumed.
        today: The last day of the window.

    Returns:
        A float rate, or None.
    """
    start = today - timedelta(days=RATE_WINDOW_DAYS)
    in_window = {
        day: qty
        for day, qty in quantities_by_day.items()
        if start <= day <= today and qty > 0
    }
    if not in_window:
        return None
    first = min(in_window)
    span_days = (today - first).days + 1
    return sum(in_window.values()) / span_days


def days_of_cover(on_hand, rate):
    """How many days the quantity on hand will last at the given daily rate.

    Returns None when there is no positive rate to divide by.
    """
    if rate is None or rate <= 0:
        return None
    return on_hand / rate


def suggested_purchase(on_hand, par, rate):
    """Quantity to buy to reach par, or a 14-day supply, whichever is larger.

    A missing rate only considers the par gap. The result is rounded up to
    the hundredth so a small gap is not rounded away to zero.
    """
    gap = max(par - on_hand, 0)
    if rate is not None and rate > 0:
        gap = max(gap, rate * COVER_TARGET_DAYS - on_hand)
    if gap <= 0:
        return 0
    return math.ceil(gap * 100) / 100


def restock_reasons(on_hand, par, cover):
    """Short labels explaining why a product should be bought again.

    A product is short when quantity on hand is below par, or when the days
    of cover are under 7. An unknown cover never triggers the second reason.
    """
    reasons = []
    if on_hand < par:
        reasons.append("Below par")
    if cover is not None and cover < RESTOCK_DAYS:
        reasons.append("Less than 7 days of cover")
    return reasons


def waste_share(consumed, wasted):
    """Fraction of handled food that was wasted. None when nothing was handled."""
    total = consumed + wasted
    if total <= 0:
        return None
    return wasted / total


def week_starts(today, count=USAGE_WEEKS):
    """Monday dates for the last `count` weeks, ending with the current week."""
    this_week = today - timedelta(days=today.weekday())
    first = this_week - timedelta(weeks=count - 1)
    return [first + timedelta(weeks=index) for index in range(count)]


def list_locations(conn):
    """Return every storage place, ordered by name."""
    rows = conn.execute("SELECT * FROM locations ORDER BY name").fetchall()
    return [_location(row) for row in rows]


def create_location(conn, name, kind):
    """Add a fridge, freezer, pantry, or other place.

    Args:
        name: Display name. Must be unique.
        kind: One of fridge, freezer, pantry, other.

    Returns:
        The stored location.
    """
    clean_name = _clean_name(name, "Name")
    clean_kind = _kind(kind)
    try:
        row = conn.execute(
            """
            INSERT INTO locations (name, kind, created_at)
            VALUES (?, ?, ?)
            RETURNING *
            """,
            (clean_name, clean_kind, current_day().isoformat()),
        ).fetchone()
    except sqlite3.IntegrityError as exc:
        raise InventoryError("A place with that name already exists", 409) from exc
    return _location(row)


def update_location(conn, location_id, name, kind):
    """Rename a place or change its kind."""
    _require_location(conn, location_id)
    clean_name = _clean_name(name, "Name")
    clean_kind = _kind(kind)
    try:
        row = conn.execute(
            """
            UPDATE locations SET name = ?, kind = ? WHERE id = ? RETURNING *
            """,
            (clean_name, clean_kind, location_id),
        ).fetchone()
    except sqlite3.IntegrityError as exc:
        raise InventoryError("A place with that name already exists", 409) from exc
    return _location(row)


def delete_location(conn, location_id):
    """Remove a place that has no food, no history, and no product pointing at it."""
    _require_location(conn, location_id)
    active = _count(conn, "SELECT COUNT(*) AS n FROM lots WHERE location_id = ? AND status = 'active'", location_id)
    if active:
        raise InventoryError("This place still has food in it", 409)
    history = _count(conn, "SELECT COUNT(*) AS n FROM lots WHERE location_id = ?", location_id)
    history += _count(conn, "SELECT COUNT(*) AS n FROM events WHERE location_id = ?", location_id)
    if history:
        raise InventoryError("This place is part of the household history and cannot be deleted", 409)
    preferred = _count(conn, "SELECT COUNT(*) AS n FROM products WHERE preferred_location_id = ?", location_id)
    if preferred:
        raise InventoryError("A product still uses this as its usual place", 409)
    _delete_row(conn, "DELETE FROM locations WHERE id = ?", location_id)


def list_products(conn):
    """Return the product catalog, ordered by name."""
    rows = conn.execute("SELECT * FROM products ORDER BY name").fetchall()
    return [_product(row) for row in rows]


def create_product(conn, name, category, unit, shelf_life_days, par_quantity, preferred_location_id=None):
    """Add a catalog item that later stock lots will copy shelf life from.

    preferred_location_id may be omitted. When present, that place must exist.
    """
    fields = _product_fields(conn, name, category, unit, shelf_life_days, par_quantity, preferred_location_id)
    try:
        row = conn.execute(
            """
            INSERT INTO products (
                name, category, unit, shelf_life_days, par_quantity,
                preferred_location_id, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            RETURNING *
            """,
            (*fields, current_day().isoformat()),
        ).fetchone()
    except sqlite3.IntegrityError as exc:
        raise InventoryError("A product with that name already exists", 409) from exc
    return _product(row)


def update_product(conn, product_id, name, category, unit, shelf_life_days, par_quantity, preferred_location_id=None):
    """Change catalog details. Existing lots keep the expiry they were given."""
    _require_product(conn, product_id)
    fields = _product_fields(conn, name, category, unit, shelf_life_days, par_quantity, preferred_location_id)
    try:
        row = conn.execute(
            """
            UPDATE products
            SET name = ?, category = ?, unit = ?, shelf_life_days = ?,
                par_quantity = ?, preferred_location_id = ?
            WHERE id = ?
            RETURNING *
            """,
            (*fields, product_id),
        ).fetchone()
    except sqlite3.IntegrityError as exc:
        raise InventoryError("A product with that name already exists", 409) from exc
    return _product(row)


def delete_product(conn, product_id):
    """Remove a product that has never been stocked."""
    _require_product(conn, product_id)
    history = _count(conn, "SELECT COUNT(*) AS n FROM events WHERE product_id = ?", product_id)
    history += _count(conn, "SELECT COUNT(*) AS n FROM lots WHERE product_id = ?", product_id)
    if history:
        raise InventoryError("This product has history and cannot be deleted", 409)
    _delete_row(conn, "DELETE FROM products WHERE id = ?", product_id)


def list_lots(conn, location_id=None):
    """Return active lots, optionally limited to one place.

    A location id that does not exist is an error. Expired lots stay in this
    list until someone records them as used or wasted.
    """
    params = []
    sql = _LOT_SQL + " WHERE lots.status = 'active'"
    if location_id is not None:
        _require_location(conn, location_id)
        sql += " AND lots.location_id = ?"
        params.append(location_id)
    sql += " ORDER BY lots.expires_on, products.name"
    return [_lot(row) for row in conn.execute(sql, params).fetchall()]


def stock(conn, product_id, location_id, quantity, added_on=None, expires_on=None):
    """Put a new lot on a shelf and record a stocked event.

    When expires_on is omitted, expiry is the added date plus the product's
    shelf-life days. That default is the shelf-life rule for a new purchase.
    """
    product = _require_product(conn, product_id)
    _require_location(conn, location_id)
    qty = _positive(quantity, "quantity")
    added = _as_date(added_on, "added_on") if added_on else current_day()
    if expires_on:
        expires = _as_date(expires_on, "expires_on")
    else:
        expires = added + timedelta(days=product["shelf_life_days"])
    if expires < added:
        raise InventoryError("Expiry cannot be before the day it was stocked")
    row = conn.execute(
        """
        INSERT INTO lots (
            product_id, location_id, quantity_added, quantity_remaining,
            added_on, expires_on, status
        )
        VALUES (?, ?, ?, ?, ?, ?, 'active')
        RETURNING id
        """,
        (product_id, location_id, qty, qty, added.isoformat(), expires.isoformat()),
    ).fetchone()
    _record_event(conn, product_id, row["id"], location_id, "stocked", qty, added, "")
    return _get_lot(conn, row["id"])


def consume(conn, lot_id, quantity, occurred_on=None):
    """Use some of a lot. The last of it marks the lot depleted."""
    return _draw(conn, lot_id, quantity, "consumed", "depleted", occurred_on, "")


def waste(conn, lot_id, quantity, occurred_on=None, notes=""):
    """Throw some of a lot away. The last of it marks the lot wasted."""
    return _draw(conn, lot_id, quantity, "wasted", "wasted", occurred_on, notes or "")


def move(conn, lot_id, location_id):
    """Move the remaining quantity of an active lot to another place."""
    lot = _require_active_lot(conn, lot_id)
    destination = _id(location_id, "location_id")
    _require_location(conn, destination)
    if destination == lot["location_id"]:
        raise InventoryError("That food is already stored there")
    conn.execute("UPDATE lots SET location_id = ? WHERE id = ?", (destination, lot_id))
    _record_event(
        conn,
        lot["product_id"],
        lot_id,
        destination,
        "moved",
        lot["quantity_remaining"],
        current_day(),
        "",
    )
    return _get_lot(conn, lot_id)


def insights(conn, today=None):
    """Dashboard, replenishment, usage, and waste figures for one day.

    Args:
        today: The day to treat as current. Defaults to current_day().

    Returns:
        A dict with summary counts, expiring lots, restock rows, an 8-week
        usage series, per-product usage, and waste totals.
    """
    today = today or current_day()
    products = list_products(conn)
    lots = list_lots(conn)
    events = _all_events(conn)
    on_hand = {}
    for lot in lots:
        on_hand[lot["product_id"]] = round(on_hand.get(lot["product_id"], 0) + lot["quantity_remaining"], 4)

    consumed_by_product = {}
    for event in events:
        if event["event_type"] != "consumed":
            continue
        day = date.fromisoformat(event["occurred_on"])
        bucket = consumed_by_product.setdefault(event["product_id"], {})
        bucket[day] = bucket.get(day, 0) + event["quantity"]

    replenishment = []
    for product in products:
        held = on_hand.get(product["id"], 0)
        rate = consumption_rate(consumed_by_product.get(product["id"], {}), today)
        cover = days_of_cover(held, rate)
        reasons = restock_reasons(held, product["par_quantity"], cover)
        replenishment.append({
            "product_id": product["id"],
            "name": product["name"],
            "unit": product["unit"],
            "par_quantity": product["par_quantity"],
            "on_hand": held,
            "daily_rate": _round_or_none(rate, 4),
            "days_of_cover": _round_or_none(cover, 1),
            "suggested_quantity": suggested_purchase(held, product["par_quantity"], rate),
            "restock": bool(reasons),
            "reasons": reasons,
        })

    expiring = [
        lot for lot in lots
        if date.fromisoformat(lot["expires_on"]) <= today + timedelta(days=RESTOCK_DAYS)
    ]
    weeks = week_starts(today)
    usage_by_week, usage_by_product = _usage(products, events, weeks)
    waste_rows, waste_month = _waste(events, products, today)
    return {
        "summary": {
            "active_lots": len(lots),
            "products_on_hand": sum(1 for qty in on_hand.values() if qty > 0),
            "expiring_soon": len(expiring),
            "restock_needed": sum(1 for row in replenishment if row["restock"]),
            "waste_events_this_month": len(waste_month),
        },
        "expiring": expiring,
        "restock": [row for row in replenishment if row["restock"]],
        "replenishment": replenishment,
        "usage_by_week": usage_by_week,
        "usage_by_product": usage_by_product,
        "waste": waste_rows,
        "waste_this_month": waste_month,
    }


def seed_demo(conn, today=None):
    """Insert a household with history, something expiring, and a shortage.

    Called only when the product table is empty. Dates are relative to today
    so the demo still shows an expiring lot and a monthly waste whenever the
    app is opened.
    """
    today = today or current_day()
    fridge = create_location(conn, "Fridge", "fridge")["id"]
    freezer = create_location(conn, "Freezer", "freezer")["id"]
    pantry = create_location(conn, "Pantry", "pantry")["id"]

    milk = create_product(conn, "Milk", "Dairy", "gal", 10, 1, fridge)["id"]
    eggs = create_product(conn, "Eggs", "Dairy", "dozen", 21, 1, fridge)["id"]
    bread = create_product(conn, "Bread", "Bakery", "loaf", 6, 1, pantry)["id"]
    chicken = create_product(conn, "Chicken breast", "Meat", "lb", 3, 2, fridge)["id"]
    peas = create_product(conn, "Frozen peas", "Frozen", "bag", 180, 1, freezer)["id"]
    rice = create_product(conn, "Rice", "Pantry", "lb", 365, 2, pantry)["id"]
    spinach = create_product(conn, "Spinach", "Produce", "bag", 5, 1, fridge)["id"]

    for weeks_ago in range(7, 0, -1):
        added = today - timedelta(weeks=weeks_ago)
        lot = stock(conn, milk, fridge, 1, added, added + timedelta(days=10))
        consume(conn, lot["id"], 1, added + timedelta(days=3))

    stock(conn, milk, fridge, 0.5, today - timedelta(days=2), today + timedelta(days=3))
    stock(conn, eggs, fridge, 1, today - timedelta(days=1))
    stock(conn, bread, pantry, 1, today - timedelta(days=1))
    stock(conn, chicken, fridge, 1.5, today - timedelta(days=1), today + timedelta(days=2))
    stock(conn, peas, freezer, 2, today - timedelta(days=10))
    stock(conn, rice, pantry, 4, today - timedelta(days=20))
    stock(conn, spinach, fridge, 1, today - timedelta(days=4), today + timedelta(days=1))

    tossed = stock(conn, spinach, fridge, 1, today - timedelta(days=8), today - timedelta(days=3))
    waste(conn, tossed["id"], 1, today - timedelta(days=6), "Wilted")
    stale = stock(conn, bread, pantry, 1, today - timedelta(days=18), today - timedelta(days=12))
    waste(conn, stale["id"], 1, today - timedelta(days=14), "Mold")


def _draw(conn, lot_id, quantity, event_type, empty_status, occurred_on, notes):
    lot = _require_active_lot(conn, lot_id)
    qty = _positive(quantity, "quantity")
    if qty > lot["quantity_remaining"]:
        raise InventoryError("That is more than what is left")
    when = _as_date(occurred_on, "occurred_on") if occurred_on else current_day()
    remaining = round(lot["quantity_remaining"] - qty, 4)
    status = "active" if remaining > 0 else empty_status
    conn.execute(
        "UPDATE lots SET quantity_remaining = ?, status = ? WHERE id = ?",
        (remaining, status, lot["id"]),
    )
    _record_event(conn, lot["product_id"], lot["id"], lot["location_id"], event_type, qty, when, notes)
    return _get_lot(conn, lot["id"])


def _usage(products, events, weeks):
    week_totals = [0.0] * len(weeks)
    product_totals = {product["id"]: [0.0] * len(weeks) for product in products}
    for event in events:
        if event["event_type"] != "consumed":
            continue
        index = _week_index(date.fromisoformat(event["occurred_on"]), weeks)
        if index is None:
            continue
        week_totals[index] = round(week_totals[index] + event["quantity"], 4)
        if event["product_id"] in product_totals:
            series = product_totals[event["product_id"]]
            series[index] = round(series[index] + event["quantity"], 4)
    usage_by_week = [
        {"week_start": start.isoformat(), "consumed": week_totals[index]}
        for index, start in enumerate(weeks)
    ]
    usage_by_product = [
        {
            "product_id": product["id"],
            "name": product["name"],
            "unit": product["unit"],
            "consumed": product_totals[product["id"]],
        }
        for product in products
        if sum(product_totals[product["id"]]) > 0
    ]
    return usage_by_week, usage_by_product


def _waste(events, products, today):
    names = {product["id"]: product for product in products}
    consumed = {}
    wasted = {}
    month = []
    for event in events:
        product_id = event["product_id"]
        if event["event_type"] == "consumed":
            consumed[product_id] = consumed.get(product_id, 0) + event["quantity"]
        elif event["event_type"] == "wasted":
            wasted[product_id] = wasted.get(product_id, 0) + event["quantity"]
            occurred = date.fromisoformat(event["occurred_on"])
            if occurred.year == today.year and occurred.month == today.month:
                product = names.get(product_id)
                month.append({
                    "product_name": product["name"] if product else "Unknown",
                    "unit": product["unit"] if product else "",
                    "quantity": event["quantity"],
                    "occurred_on": event["occurred_on"],
                    "notes": event["notes"],
                })
    rows = []
    for product in products:
        used = round(consumed.get(product["id"], 0), 4)
        tossed = round(wasted.get(product["id"], 0), 4)
        if used == 0 and tossed == 0:
            continue
        share = waste_share(used, tossed)
        rows.append({
            "product_id": product["id"],
            "name": product["name"],
            "unit": product["unit"],
            "consumed": used,
            "wasted": tossed,
            "waste_share": None if share is None else round(share, 4),
        })
    return rows, month


def _week_index(day, weeks):
    for index, start in enumerate(weeks):
        if start <= day < start + timedelta(days=7):
            return index
    return None


def _record_event(conn, product_id, lot_id, location_id, event_type, quantity, occurred_on, notes):
    conn.execute(
        """
        INSERT INTO events (
            product_id, lot_id, location_id, event_type, quantity, occurred_on, notes
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (product_id, lot_id, location_id, event_type, quantity, occurred_on.isoformat(), notes or ""),
    )


def _all_events(conn):
    return [dict(row) for row in conn.execute("SELECT * FROM events ORDER BY occurred_on, id").fetchall()]


def _product_fields(conn, name, category, unit, shelf_life_days, par_quantity, preferred_location_id):
    place_id = None
    if preferred_location_id not in (None, ""):
        place_id = _id(preferred_location_id, "preferred_location_id")
        _require_location(conn, place_id)
    return (
        _clean_name(name, "Name"),
        _clean_name(category, "Category"),
        _clean_name(unit, "Unit"),
        _whole_days(shelf_life_days),
        _non_negative(par_quantity, "par_quantity"),
        place_id,
    )


def _require_location(conn, location_id):
    number = _id(location_id, "location_id")
    row = conn.execute("SELECT * FROM locations WHERE id = ?", (number,)).fetchone()
    if row is None:
        raise InventoryError("Place was not found", 404)
    return row


def _require_product(conn, product_id):
    number = _id(product_id, "product_id")
    row = conn.execute("SELECT * FROM products WHERE id = ?", (number,)).fetchone()
    if row is None:
        raise InventoryError("Product was not found", 404)
    return row


def _require_active_lot(conn, lot_id):
    number = _id(lot_id, "lot_id")
    row = conn.execute("SELECT * FROM lots WHERE id = ?", (number,)).fetchone()
    if row is None:
        raise InventoryError("Item was not found", 404)
    if row["status"] != "active":
        raise InventoryError("That item is no longer in the kitchen")
    return row


def _get_lot(conn, lot_id):
    row = conn.execute(_LOT_SQL + " WHERE lots.id = ?", (lot_id,)).fetchone()
    return _lot(row)


_LOT_SQL = """
SELECT
    lots.*,
    products.name AS product_name,
    products.category AS category,
    products.unit AS unit,
    products.par_quantity AS par_quantity,
    products.shelf_life_days AS shelf_life_days,
    locations.name AS location_name,
    locations.kind AS location_kind
FROM lots
JOIN products ON products.id = lots.product_id
JOIN locations ON locations.id = lots.location_id
"""


def _location(row):
    return {"id": row["id"], "name": row["name"], "kind": row["kind"]}


def _product(row):
    return {
        "id": row["id"],
        "name": row["name"],
        "category": row["category"],
        "unit": row["unit"],
        "shelf_life_days": row["shelf_life_days"],
        "par_quantity": row["par_quantity"],
        "preferred_location_id": row["preferred_location_id"],
    }


def _lot(row):
    return {
        "id": row["id"],
        "product_id": row["product_id"],
        "product_name": row["product_name"],
        "category": row["category"],
        "unit": row["unit"],
        "location_id": row["location_id"],
        "location_name": row["location_name"],
        "location_kind": row["location_kind"],
        "quantity_added": row["quantity_added"],
        "quantity_remaining": row["quantity_remaining"],
        "added_on": row["added_on"],
        "expires_on": row["expires_on"],
        "status": row["status"],
        "par_quantity": row["par_quantity"],
        "shelf_life_days": row["shelf_life_days"],
    }


def _count(conn, sql, param):
    return conn.execute(sql, (param,)).fetchone()["n"]


def _delete_row(conn, sql, param):
    try:
        conn.execute(sql, (param,))
    except sqlite3.IntegrityError as exc:
        raise InventoryError("That record is still in use", 409) from exc


def _round_or_none(value, places):
    if value is None:
        return None
    return round(value, places)


def _clean_name(value, field):
    if not isinstance(value, str) or not value.strip():
        raise InventoryError(f"{field} is required")
    return value.strip()


def _kind(value):
    if value not in KINDS:
        raise InventoryError("Kind must be fridge, freezer, pantry, or other")
    return value


def _id(value, field):
    if isinstance(value, bool):
        raise InventoryError(f"{field} must be a whole number")
    try:
        number = int(value)
    except (TypeError, ValueError) as exc:
        raise InventoryError(f"{field} must be a whole number") from exc
    if number <= 0:
        raise InventoryError(f"{field} must be a whole number")
    return number


def _positive(value, field):
    number = _number(value, field)
    if number <= 0:
        raise InventoryError(f"{field} must be greater than zero")
    return number


def _non_negative(value, field):
    number = _number(value, field)
    if number < 0:
        raise InventoryError(f"{field} cannot be negative")
    return number


def _number(value, field):
    if isinstance(value, bool):
        raise InventoryError(f"{field} must be a number")
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise InventoryError(f"{field} must be a number") from exc
    return round(number, 4)


def _whole_days(value):
    if isinstance(value, bool) or not isinstance(value, int):
        raise InventoryError("Shelf life must be a whole number of days")
    if value < 0:
        raise InventoryError("Shelf life cannot be negative")
    return value


def _as_date(value, field):
    if isinstance(value, datetime):
        raise InventoryError(f"{field} must be a YYYY-MM-DD date")
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        try:
            return date.fromisoformat(value)
        except ValueError as exc:
            raise InventoryError(f"{field} must be a YYYY-MM-DD date") from exc
    raise InventoryError(f"{field} must be a YYYY-MM-DD date")
