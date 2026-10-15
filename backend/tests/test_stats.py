def test_stats_on_empty_catalogue(client):
    assert client.get("/api/stats").json() == {
        "total_skus": 0,
        "total_units": 0,
        "inventory_value": 0.0,
        "low_stock": 0,
        "out_of_stock": 0,
        "categories": [],
    }


def test_stats_totals_value_and_alerts(client, make_product):
    make_product(sku="S-1", quantity=10, reorder_level=2, unit_price="1.50", category="Office")
    make_product(sku="S-2", quantity=3, reorder_level=5, unit_price="10.00", category="Office")
    make_product(sku="S-3", quantity=0, reorder_level=1, unit_price="99.00", category="Safety")

    stats = client.get("/api/stats").json()
    assert stats["total_skus"] == 3
    assert stats["total_units"] == 13
    assert stats["inventory_value"] == 45.0
    assert stats["low_stock"] == 1
    assert stats["out_of_stock"] == 1
    assert stats["categories"][0] == {"category": "Office", "skus": 2, "units": 13, "value": 45.0}


def test_categories_are_distinct_and_sorted(client, make_product):
    make_product(sku="C-1", category="Safety")
    make_product(sku="C-2", category="Office")
    make_product(sku="C-3", category="Safety")
    assert client.get("/api/categories").json() == ["Office", "Safety"]
