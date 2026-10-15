import os

# Point the app at a throwaway in-memory SQLite DB *before* app modules are imported,
# so tests can never touch the Postgres database used by docker compose or k8s.
os.environ["DATABASE_URL"] = "sqlite+pysqlite:///:memory:"
os.environ["ENVIRONMENT"] = "test"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.database import Base, engine  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture(autouse=True)
def fresh_schema():
    Base.metadata.create_all(engine)
    yield
    Base.metadata.drop_all(engine)


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def make_product(client):
    def _make(**overrides):
        payload = {
            "sku": "TST-0001",
            "name": "Test widget",
            "category": "Testing",
            "quantity": 20,
            "reorder_level": 5,
            "unit_price": "2.50",
            "location": "Z-01",
            "supplier": "Acme",
        }
        payload.update(overrides)
        response = client.post("/api/products", json=payload)
        assert response.status_code == 201, response.text
        return response.json()

    return _make
