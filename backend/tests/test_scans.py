"""End-to-end scan workflow tests."""
from __future__ import annotations


def test_list_missions(client):
    res = client.get("/api/missions")
    assert res.status_code == 200
    assert isinstance(res.json(), list)


def test_system_info(client):
    res = client.get("/api/system/info")
    assert res.status_code == 200
    body = res.json()
    assert "model_name" in body
    assert "classes" in body
    assert "disclaimer" in body


def test_upload_and_analyze(client, auth_headers):
    import io

    import cv2
    import numpy as np

    img = (np.random.rand(256, 256) * 255).astype(np.uint8)
    ok, buf = cv2.imencode(".png", img)
    assert ok

    files = {"file": ("test.png", buf.tobytes(), "image/png")}
    res = client.post(
        "/api/scans/upload",
        files=files,
        data={"auto_analyze": "true"},
        headers=auth_headers,
    )
    assert res.status_code == 200, res.text
    scan = res.json()
    assert scan["status"] == "complete"
    assert scan["detection_count"] >= 0
    assert scan["is_demo"] is False  # user uploads are real

    # Fetch detail
    detail = client.get(f"/api/scans/{scan['id']}", headers=auth_headers)
    assert detail.status_code == 200
    assert "detections" in detail.json()


def test_upload_rejects_invalid_type(client, auth_headers):
    res = client.post(
        "/api/scans/upload",
        files={"file": ("bad.exe", b"MZ\x00\x00", "application/octet-stream")},
        headers=auth_headers,
    )
    assert res.status_code == 400


def test_compare_endpoint(client):
    res = client.post("/api/scans/compare", json={"scan_a_id": 0, "scan_b_id": 0})
    assert res.status_code == 400


def test_detection_listing(client, auth_headers):
    res = client.get("/api/detections", headers=auth_headers)
    assert res.status_code == 200
    assert isinstance(res.json(), list)


def test_analytics_summary(client):
    res = client.get("/api/analytics/summary")
    assert res.status_code == 200
    body = res.json()
    assert "real_vs_demo" in body
    assert "data_source" in body


def test_analytics_real_only(client):
    res = client.get("/api/analytics/summary?include_demo=false")
    assert res.status_code == 200


def test_hotspots(client):
    res = client.get("/api/hotspots")
    assert res.status_code == 200
    assert isinstance(res.json(), list)


def test_models_registry(client):
    res = client.get("/api/models")
    assert res.status_code == 200
    assert isinstance(res.json(), list)