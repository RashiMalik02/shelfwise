import pytest


def test_create_product_normalises_sku_and_sets_status(client):
    response = client.post(
        "/api/products",
        json={"sku": "pkg-77", "name": "  Mailer bag  ", "category": "Packaging", "quantity": 3, "reorder_level": 10},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["sku"] == "PKG-77"
    assert body["name"] == "Mailer bag"
    assert body["stock_status"] == "LOW"


def test_duplicate_sku_is_rejected(client, make_product):
    make_product(sku="DUP-1")
    response = client.post("/api/products", json={"sku": "dup-1", "name": "Other", "category": "Testing"})
    assert response.status_code == 409
    assert "already exists" in response.json()["detail"]


@pytest.mark.parametrize(
    "payload",
    [
        {"sku": "OK-1", "name": "Neg qty", "category": "Testing", "quantity": -1},
        {"sku": "bad sku!", "name": "Bad sku", "category": "Testing"},
        {"sku": "OK-2", "name": "X", "category": "Testing"},
        {"sku": "OK-3", "name": "Price", "category": "Testing", "unit_price": "-4"},
    ],
)
def test_invalid_payloads_return_422(client, payload):
    assert client.post("/api/products", json=payload).status_code == 422


def test_get_product_by_id(client, make_product):
    created = make_product()
    response = client.get(f"/api/products/{created['id']}")
    assert response.status_code == 200
    assert response.json()["sku"] == "TST-0001"


def test_get_missing_product_returns_404(client):
    assert client.get("/api/products/999").status_code == 404


def test_list_filters_by_status_category_and_search(client, make_product):
    make_product(sku="A-1", name="Healthy item", quantity=50, reorder_level=5, category="Office")
    make_product(sku="A-2", name="Low item", quantity=2, reorder_level=5, category="Office")
    make_product(sku="A-3", name="Empty item", quantity=0, reorder_level=5, category="Safety", supplier="Guardline")

    assert len(client.get("/api/products").json()) == 3
    assert [p["sku"] for p in client.get("/api/products?status=LOW").json()] == ["A-2"]
    assert [p["sku"] for p in client.get("/api/products?status=OUT").json()] == ["A-3"]
    assert [p["sku"] for p in client.get("/api/products?status=OK").json()] == ["A-1"]
    assert {p["sku"] for p in client.get("/api/products?category=Office").json()} == {"A-1", "A-2"}
    assert [p["sku"] for p in client.get("/api/products?q=guard").json()] == ["A-3"]


def test_update_product_details(client, make_product):
    created = make_product()
    response = client.put(f"/api/products/{created['id']}", json={"name": "Renamed widget", "unit_price": "3.99"})
    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "Renamed widget"
    assert body["unit_price"] == 3.99
    assert body["quantity"] == created["quantity"]


def test_update_quantity_is_logged_as_stock_count(client, make_product):
    created = make_product(quantity=20)
    client.put(f"/api/products/{created['id']}", json={"quantity": 17})
    movements = client.get(f"/api/products/{created['id']}/movements").json()
    assert movements[0]["reason"] == "COUNT"
    assert movements[0]["delta"] == -3
    assert movements[0]["quantity_after"] == 17


def test_update_missing_product_returns_404(client):
    assert client.put("/api/products/42", json={"name": "Ghost"}).status_code == 404


def test_delete_product(client, make_product):
    created = make_product()
    assert client.delete(f"/api/products/{created['id']}").status_code == 204
    assert client.get(f"/api/products/{created['id']}").status_code == 404
    assert client.delete(f"/api/products/{created['id']}").status_code == 404
