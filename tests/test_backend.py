"""HTTP tests. Rule details are covered in test_inventory.py and test_rules.py."""

import pytest

from app import create_app


@pytest.fixture
def client(tmp_path):
    application = create_app({
        "DATABASE_PATH": str(tmp_path / "api.db"),
        "SEED": False,
    })
    application.config["TESTING"] = True
    return application.test_client()


def test_health_endpoint(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    body = response.get_json()
    assert body["status"] == "healthy"
    assert "timestamp" in body


def test_cors_header(client):
    response = client.get("/api/health")
    assert "Access-Control-Allow-Origin" in response.headers


def test_stock_consume_and_reject_bad_json(client):
    place = client.post("/api/locations", json={"name": "Fridge", "kind": "fridge"})
    product = client.post("/api/products", json={
        "name": "Milk",
        "category": "Dairy",
        "unit": "gal",
        "shelf_life_days": 10,
        "par_quantity": 1,
        "preferred_location_id": place.get_json()["id"],
    })
    assert product.status_code == 201
    lot = client.post("/api/inventory/stock", json={
        "product_id": product.get_json()["id"],
        "location_id": place.get_json()["id"],
        "quantity": 1,
        "added_on": "2026-10-01",
    })
    assert lot.status_code == 201
    assert lot.get_json()["expires_on"] == "2026-10-11"

    used = client.post("/api/inventory/consume", json={"lot_id": lot.get_json()["id"], "quantity": 1})
    assert used.status_code == 200
    assert used.get_json()["status"] == "depleted"

    rejected = client.post("/api/inventory/stock", data="nope", content_type="text/plain")
    assert rejected.status_code == 400
    assert "error" in rejected.get_json()


def test_missing_lot_and_delete_guard(client):
    missing = client.post("/api/inventory/waste", json={"lot_id": 5, "quantity": 1})
    assert missing.status_code == 404

    place = client.post("/api/locations", json={"name": "Pantry", "kind": "pantry"})
    product = client.post("/api/products", json={
        "name": "Rice",
        "category": "Pantry",
        "unit": "lb",
        "shelf_life_days": 365,
        "par_quantity": 1,
        "preferred_location_id": place.get_json()["id"],
    })
    client.post("/api/inventory/stock", json={
        "product_id": product.get_json()["id"],
        "location_id": place.get_json()["id"],
        "quantity": 1,
    })
    blocked = client.delete(f"/api/products/{product.get_json()['id']}")
    assert blocked.status_code == 409
    removed = client.delete("/api/locations/999")
    assert removed.status_code == 404


def test_seeded_database_reports_a_shortage(tmp_path):
    application = create_app({
        "DATABASE_PATH": str(tmp_path / "demo.db"),
        "SEED": True,
    })
    client = application.test_client()
    response = client.get("/api/insights")
    assert response.status_code == 200
    summary = response.get_json()["summary"]
    assert summary["expiring_soon"] >= 1
    assert summary["restock_needed"] >= 1
    listed = client.get("/api/inventory")
    assert listed.status_code == 200
    assert len(listed.get_json()) >= 1
