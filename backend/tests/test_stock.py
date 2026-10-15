def test_receiving_stock_increases_quantity(client, make_product):
    product = make_product(quantity=4, reorder_level=5)
    assert product["stock_status"] == "LOW"

    response = client.post(f"/api/products/{product['id']}/adjust", json={"delta": 30, "reason": "RECEIVED"})
    assert response.status_code == 200
    assert response.json()["quantity"] == 34
    assert response.json()["stock_status"] == "OK"


def test_selling_everything_marks_product_out_of_stock(client, make_product):
    product = make_product(quantity=6)
    response = client.post(f"/api/products/{product['id']}/adjust", json={"delta": -6, "reason": "SOLD"})
    assert response.json()["quantity"] == 0
    assert response.json()["stock_status"] == "OUT"


def test_cannot_remove_more_than_on_hand(client, make_product):
    product = make_product(quantity=2)
    response = client.post(f"/api/products/{product['id']}/adjust", json={"delta": -3, "reason": "SOLD"})
    assert response.status_code == 409
    assert client.get(f"/api/products/{product['id']}").json()["quantity"] == 2


def test_zero_delta_and_unknown_reason_are_rejected(client, make_product):
    product = make_product()
    url = f"/api/products/{product['id']}/adjust"
    assert client.post(url, json={"delta": 0, "reason": "SOLD"}).status_code == 422
    assert client.post(url, json={"delta": 1, "reason": "STOLEN"}).status_code == 422


def test_movement_ledger_is_newest_first(client, make_product):
    product = make_product(sku="LED-1", quantity=10)
    url = f"/api/products/{product['id']}/adjust"
    client.post(url, json={"delta": -4, "reason": "SOLD", "note": "Order 1182"})
    client.post(url, json={"delta": -1, "reason": "DAMAGED"})

    ledger = client.get("/api/movements?limit=10").json()
    assert [m["reason"] for m in ledger] == ["DAMAGED", "SOLD", "RECEIVED"]
    assert [m["quantity_after"] for m in ledger] == [5, 6, 10]
    assert ledger[1]["note"] == "Order 1182"
    assert ledger[0]["sku"] == "LED-1"


def test_deleting_product_removes_its_movements(client, make_product):
    product = make_product(quantity=5)
    client.delete(f"/api/products/{product['id']}")
    assert client.get("/api/movements").json() == []
