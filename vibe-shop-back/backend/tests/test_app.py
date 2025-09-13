import sys
from pathlib import Path
import json
from fastapi.testclient import TestClient

# Ensure project root is on the path
sys.path.append(str(Path(__file__).resolve().parents[2]))

from backend.main import app

client = TestClient(app)


def test_health():
    response = client.get("/health/live")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_products():
    response = client.get("/products")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    products_path = Path(__file__).resolve().parents[1] / "static" / "products.json"
    with products_path.open("r", encoding="utf-8") as f:
        expected = json.load(f)
    assert data == expected
