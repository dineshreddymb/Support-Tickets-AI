import time
import os
from fastapi.testclient import TestClient
from app import app

client = TestClient(app)


def test_query_count_unresolved():
    start = time.time()
    resp = client.post("/query", json={"question": "How many tickets are unresolved?"})
    elapsed = time.time() - start
    assert resp.status_code == 200
    data = resp.json()
    assert "count" in data or "preview" in data
    assert elapsed < 5.0


def test_anomalies_endpoint_performance():
    start = time.time()
    resp = client.get("/anomalies")
    elapsed = time.time() - start
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, dict)
    assert elapsed < 5.0
