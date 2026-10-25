"""Integration tests: the whole API through HTTP, with the REAL trained model.

These tests describe the behaviour the app depends on (status codes, messages, response shape),
so they stay the same when the internal code is reorganised.
Run from the repo root:  python -m pytest backend/tests -q
"""
import base64
import io
import uuid

import pytest
from conftest import blurry_image, jpeg_bytes, png_bytes, textured_image
from fastapi.testclient import TestClient
from PIL import Image

from app.main import app  # noqa: E402  (imported after conftest has set the environment)

CLASS_CODES = {"akiec", "bcc", "bkl", "df", "mel", "nv", "vasc"}
DISCLAIMER = "Decision-support prototype only. Not a diagnosis. Consult a qualified clinician."


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:          # runs startup: creates tables, loads the model
        yield c


def new_user(client, password="password123"):
    email = f"user-{uuid.uuid4().hex[:10]}@test.local"
    r = client.post("/auth/register", json={"email": email, "password": password})
    assert r.status_code == 201, r.text
    return email, {"Authorization": f"Bearer {r.json()['access_token']}"}


def upload(client, headers, data, content_type="image/jpeg", name="lesion.jpg"):
    return client.post("/predict", headers=headers, files={"image": (name, data, content_type)})


# ---------------- system ----------------
def test_health_reports_model_loaded(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok" and r.json()["model_loaded"] is True


def test_swagger_docs_available(client):
    assert client.get("/docs").status_code == 200
    assert "/predict" in client.get("/openapi.json").json()["paths"]


# ---------------- authentication ----------------
def test_register_and_login(client):
    email, _ = new_user(client)
    r = client.post("/auth/login", data={"username": email, "password": "password123"})
    assert r.status_code == 200 and r.json()["token_type"] == "bearer"


def test_register_rejects_duplicate_email(client):
    email, _ = new_user(client)
    r = client.post("/auth/register", json={"email": email, "password": "password123"})
    assert r.status_code == 409


@pytest.mark.parametrize("email,password", [("not-an-email", "password123"), ("ok@test.local", "short")])
def test_register_rejects_bad_input(client, email, password):
    assert client.post("/auth/register", json={"email": email, "password": password}).status_code == 422


def test_login_rejects_wrong_password(client):
    email, _ = new_user(client)
    r = client.post("/auth/login", data={"username": email, "password": "wrong-password"})
    assert r.status_code == 401


@pytest.mark.parametrize("headers", [{}, {"Authorization": "Bearer not-a-real-token"}])
def test_predict_requires_valid_token(client, headers):
    r = upload(client, headers, jpeg_bytes(textured_image()))
    assert r.status_code == 401


# ---------------- input validation (different inputs and error handling) ----------------
def test_rejects_wrong_file_type(client):
    _, h = new_user(client)
    r = upload(client, h, b"not an image", content_type="text/plain", name="notes.txt")
    assert r.status_code == 415 and "JPEG or PNG" in r.json()["detail"]


def test_rejects_oversized_file(client):
    _, h = new_user(client)
    r = upload(client, h, b"\xff" * (8 * 1024 * 1024 + 1))
    assert r.status_code == 413 and "too large" in r.json()["detail"]


def test_rejects_corrupted_image(client):
    _, h = new_user(client)
    r = upload(client, h, b"\xff\xd8\xff\xe0 this is not really a jpeg")
    assert r.status_code == 400 and "could not be read" in r.json()["detail"]


def test_rejects_low_resolution(client):
    _, h = new_user(client)
    r = upload(client, h, jpeg_bytes(textured_image(size=(100, 100))))
    assert r.status_code == 422 and "resolution is too low" in r.json()["detail"]


def test_rejects_blurry_image(client):
    _, h = new_user(client)
    r = upload(client, h, jpeg_bytes(blurry_image()))
    assert r.status_code == 422 and "too blurry" in r.json()["detail"]


def test_accepts_png_with_transparency(client):
    _, h = new_user(client)
    rgba = textured_image().convert("RGBA")
    r = upload(client, h, png_bytes(rgba), content_type="image/png", name="lesion.png")
    assert r.status_code == 200, r.text


# ---------------- prediction ----------------
def test_prediction_response_contract(client, sample_lesion_bytes):
    _, h = new_user(client)
    r = upload(client, h, sample_lesion_bytes)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["predicted_class"] in CLASS_CODES
    assert set(body["probabilities"]) == CLASS_CODES
    assert abs(sum(body["probabilities"].values()) - 1.0) < 1e-3
    assert body["predicted_class"] == max(body["probabilities"], key=body["probabilities"].get)
    assert body["entropy"] >= 0 and body["entropy_threshold"] > 0
    assert isinstance(body["review_recommended"], bool) and body["review_reason"]
    assert body["disclaimer"] == DISCLAIMER
    assert body["inference_ms"] > 0
    heatmap = Image.open(io.BytesIO(base64.b64decode(body["heatmap_base64"])))
    assert heatmap.format == "PNG" and heatmap.size == (300, 300)


def test_review_flag_matches_reason(client, sample_lesion_bytes):
    _, h = new_user(client)
    body = upload(client, h, sample_lesion_bytes).json()
    if body["review_recommended"]:
        assert "uncertainty" in body["review_reason"].lower() or "melanoma" in body["review_reason"].lower()
    else:
        assert body["review_reason"] == "No review trigger met."


# ---------------- case history ----------------
def test_case_history_is_private_to_each_user(client, sample_lesion_bytes):
    _, alice = new_user(client)
    _, bob = new_user(client)
    case = upload(client, alice, sample_lesion_bytes).json()

    listed = client.get("/cases", headers=alice).json()
    assert [c["case_id"] for c in listed] == [case["case_id"]]

    again = client.get(f"/cases/{case['case_id']}", headers=alice)
    assert again.status_code == 200
    assert again.json()["predicted_class"] == case["predicted_class"]
    assert again.json()["heatmap_base64"] == case["heatmap_base64"]

    assert client.get("/cases", headers=bob).json() == []
    assert client.get(f"/cases/{case['case_id']}", headers=bob).status_code == 404
    assert client.get("/cases/999999", headers=alice).status_code == 404
