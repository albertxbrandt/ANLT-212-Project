"""HTTP routes for PantryPal.

Routes read JSON, call inventory.py, and return JSON. They do not apply
stock, waste, or replenishment rules themselves.
"""

import os
from datetime import datetime, timezone

from dotenv import load_dotenv
from flask import Flask, jsonify, request
from flask_cors import CORS

from db import DEFAULT_PATH, init_db, session
from inventory import (
    InventoryError,
    consume,
    create_location,
    create_product,
    delete_location,
    delete_product,
    insights,
    list_locations,
    list_lots,
    list_products,
    move,
    stock,
    update_location,
    update_product,
    waste,
)


def create_app(config=None):
    """Build a Flask app bound to one SQLite file.

    Args:
        config: Optional overrides for DATABASE_PATH and SEED. SEED defaults
            to True so a first launch has a demo household. Tests pass
            SEED False and a temporary path.

    Returns:
        A Flask application. Tables are created on the first request.
    """
    load_dotenv()
    application = Flask(__name__)
    CORS(application)
    overrides = config or {}
    application.config["DATABASE_PATH"] = overrides.get("DATABASE_PATH") or os.getenv("DATABASE_PATH") or DEFAULT_PATH
    if "SEED" in overrides:
        application.config["SEED"] = bool(overrides["SEED"])
    else:
        application.config["SEED"] = os.getenv("INVENTORY_SEED", "1") != "0"
    application.config["READY"] = set()
    _register(application)
    return application


def _register(application):
    @application.before_request
    def prepare_database():
        path = application.config["DATABASE_PATH"]
        if path in application.config["READY"]:
            return
        with session(path) as conn:
            init_db(conn, seed=application.config["SEED"])
        application.config["READY"].add(path)

    @application.errorhandler(InventoryError)
    def handle_inventory_error(err):
        return jsonify({"error": str(err)}), err.status

    @application.get("/api/health")
    def health():
        """Report that the API process is answering."""
        return jsonify({
            "status": "healthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

    @application.get("/api/locations")
    def get_locations():
        with session(application.config["DATABASE_PATH"]) as conn:
            return jsonify(list_locations(conn))

    @application.post("/api/locations")
    def post_location():
        data = _json_object()
        with session(application.config["DATABASE_PATH"]) as conn:
            created = create_location(conn, data.get("name"), data.get("kind"))
        return jsonify(created), 201

    @application.put("/api/locations/<int:location_id>")
    def put_location(location_id):
        data = _json_object()
        with session(application.config["DATABASE_PATH"]) as conn:
            updated = update_location(conn, location_id, data.get("name"), data.get("kind"))
        return jsonify(updated)

    @application.delete("/api/locations/<int:location_id>")
    def remove_location(location_id):
        with session(application.config["DATABASE_PATH"]) as conn:
            delete_location(conn, location_id)
        return "", 204

    @application.get("/api/products")
    def get_products():
        with session(application.config["DATABASE_PATH"]) as conn:
            return jsonify(list_products(conn))

    @application.post("/api/products")
    def post_product():
        data = _json_object()
        with session(application.config["DATABASE_PATH"]) as conn:
            created = create_product(conn, **_product_kwargs(data))
        return jsonify(created), 201

    @application.put("/api/products/<int:product_id>")
    def put_product(product_id):
        data = _json_object()
        with session(application.config["DATABASE_PATH"]) as conn:
            updated = update_product(conn, product_id, **_product_kwargs(data))
        return jsonify(updated)

    @application.delete("/api/products/<int:product_id>")
    def remove_product(product_id):
        with session(application.config["DATABASE_PATH"]) as conn:
            delete_product(conn, product_id)
        return "", 204

    @application.get("/api/inventory")
    def get_inventory():
        location_id = request.args.get("location_id")
        with session(application.config["DATABASE_PATH"]) as conn:
            lots = list_lots(conn, location_id if location_id else None)
        return jsonify(lots)

    @application.post("/api/inventory/stock")
    def post_stock():
        data = _json_object()
        with session(application.config["DATABASE_PATH"]) as conn:
            lot = stock(
                conn,
                data.get("product_id"),
                data.get("location_id"),
                data.get("quantity"),
                data.get("added_on"),
                data.get("expires_on"),
            )
        return jsonify(lot), 201

    @application.post("/api/inventory/consume")
    def post_consume():
        data = _json_object()
        with session(application.config["DATABASE_PATH"]) as conn:
            lot = consume(conn, data.get("lot_id"), data.get("quantity"), data.get("occurred_on"))
        return jsonify(lot)

    @application.post("/api/inventory/waste")
    def post_waste():
        data = _json_object()
        with session(application.config["DATABASE_PATH"]) as conn:
            lot = waste(
                conn,
                data.get("lot_id"),
                data.get("quantity"),
                data.get("occurred_on"),
                data.get("notes") or "",
            )
        return jsonify(lot)

    @application.post("/api/inventory/move")
    def post_move():
        data = _json_object()
        with session(application.config["DATABASE_PATH"]) as conn:
            lot = move(conn, data.get("lot_id"), data.get("location_id"))
        return jsonify(lot)

    @application.get("/api/insights")
    def get_insights():
        with session(application.config["DATABASE_PATH"]) as conn:
            return jsonify(insights(conn))


def _json_object():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        raise InventoryError("Expected a JSON object")
    return data


def _product_kwargs(data):
    """Map a product request body onto create_product and update_product."""
    return {
        "name": data.get("name"),
        "category": data.get("category"),
        "unit": data.get("unit"),
        "shelf_life_days": data.get("shelf_life_days"),
        "par_quantity": data.get("par_quantity"),
        "preferred_location_id": data.get("preferred_location_id"),
    }


app = create_app()


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    print(f"\n{'=' * 50}")
    print(f"PantryPal API on http://localhost:{port}")
    print(f"{'=' * 50}\n")
    app.run(host="localhost", port=port, debug=os.getenv("FLASK_DEBUG", "True") == "True")
