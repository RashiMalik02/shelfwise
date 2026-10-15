def test_health_is_up(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "UP"}


def test_ready_when_database_reachable(client):
    response = client.get("/ready")
    assert response.status_code == 200
    assert response.json()["status"] == "READY"


def test_ready_returns_503_without_schema(client):
    from app.database import Base, engine

    Base.metadata.drop_all(engine)
    response = client.get("/ready")
    assert response.status_code == 503
    assert response.json()["status"] == "NOT_READY"


def test_root_describes_service(client):
    body = client.get("/").json()
    assert body["service"] == "Shelfwise API"
    assert body["docs"] == "/docs"


def test_metrics_exposes_http_and_inventory_metrics(client, make_product):
    make_product()
    client.get("/api/products")
    text = client.get("/metrics").text
    assert "http_requests_total" in text
    assert "http_request_duration_seconds_bucket" in text
    assert "shelfwise_products 1.0" in text
    assert 'shelfwise_stock_movements_total{reason="RECEIVED"}' in text


def test_api_info_reports_environment(client):
    assert client.get("/api/info").json()["environment"] == "test"
