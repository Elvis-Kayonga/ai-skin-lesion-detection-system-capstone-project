"""End-to-end smoke test against a running API (for example the Docker Compose stack).

Usage (from the repo root, with the stack running):
    python backend/scripts/smoke_test.py http://localhost:8000

Checks /health, registers a throwaway account, runs /predict on a sample image and reads /cases.
"""
import json
import secrets
import sys
import time
import urllib.request
import uuid
from pathlib import Path

IMAGE = Path(__file__).resolve().parents[2] / "sample_images" / "ISIC_0030440.jpg"


def call(api, method, path, body=None, headers=None, ctype="application/json"):
    req = urllib.request.Request(api + path, data=body, method=method, headers=headers or {})
    if body is not None:
        req.add_header("Content-Type", ctype)
    with urllib.request.urlopen(req, timeout=600) as r:
        return json.loads(r.read())


def main(api: str) -> None:
    for _ in range(120):
        try:
            health = call(api, "GET", "/health")
            break
        except OSError:
            time.sleep(5)
    else:
        sys.exit("API did not answer /health")
    print("health:", health)

    creds = {"email": f"smoke_{secrets.token_hex(4)}@example.com", "password": secrets.token_urlsafe(16)}
    token = call(api, "POST", "/auth/register", json.dumps(creds).encode())["access_token"]
    auth = {"Authorization": "Bearer " + token}

    boundary = uuid.uuid4().hex
    body = (f'--{boundary}\r\nContent-Disposition: form-data; name="image"; filename="{IMAGE.name}"\r\n'
            "Content-Type: image/jpeg\r\n\r\n").encode() + IMAGE.read_bytes() + f"\r\n--{boundary}--\r\n".encode()
    for attempt in (1, 2):
        result = call(api, "POST", "/predict", body, auth, f"multipart/form-data; boundary={boundary}")
        print(f"predict {attempt}:", {k: result[k] for k in ("case_id", "predicted_class", "review_recommended", "inference_ms")})
    print("cases stored for this account:", len(call(api, "GET", "/cases", headers=auth)))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000")
