"""Unit tests for the services with stand-in parts (no trained model, no real files).

Because `ScreeningService` depends on the `LesionClassifier` and `Explainer` interfaces rather than on
EfficientNet itself, a tiny fake classifier can be passed in. These tests run in milliseconds.
"""
import base64
from types import SimpleNamespace

import numpy as np
import pytest
from conftest import jpeg_bytes, textured_image

from app.core.errors import (
    AuthenticationFailed,
    Conflict,
    ImageRejected,
    InvalidInput,
    ModelNotReady,
    NotFound,
)
from app.ml.classifier import LesionClassifier, Prediction
from app.ml.explainer import Explainer
from app.ml.model_config import ModelConfig
from app.ml.uncertainty import predictive_entropy
from app.quality import FileTypeCheck, ImageValidator
from app.security import PasswordHasher, TokenService
from app.services import AuthService, ScreeningService

CONFIG = ModelConfig(input_size=300, mean=[0.5] * 3, std=[0.5] * 3,
                     class_codes=["akiec", "bcc", "bkl", "df", "mel", "nv", "vasc"],
                     class_names=["AK", "BCC", "BKL", "DF", "Melanoma", "Nevus", "Vascular"],
                     mc_dropout_passes=10, entropy_threshold=0.4129, melanoma_flag_threshold=0.05, melanoma_index=4)


class FakeClassifier(LesionClassifier):
    def __init__(self, probabilities, ready=True):
        self.p, self._ready = np.asarray(probabilities, dtype=float), ready

    def load(self): pass

    @property
    def ready(self): return self._ready

    @property
    def config(self): return CONFIG if self._ready else None

    @property
    def error(self): return None if self._ready else "no model"

    def predict(self, image):
        if not self._ready:
            raise ModelNotReady("Model not available: no model")
        return Prediction(self.p, predictive_entropy(self.p))


class FakeExplainer(Explainer):
    def explain(self, image, class_index):
        return b"PNG-heatmap-for-%d" % class_index


class FakeStore:
    def __init__(self): self.files = {}

    def save_case_files(self, image, heatmap_png):
        n = len(self.files)
        self.files[f"img{n}.jpg"], self.files[f"cam{n}.png"] = b"jpg", heatmap_png
        return f"img{n}.jpg", f"cam{n}.png"

    def read(self, path): return self.files[path]


class FakeCases:
    """In-memory stand-in for CaseRepository."""

    def __init__(self): self.rows = []

    def add(self, user_id, image_path, result, heatmap_path):
        case = SimpleNamespace(id=len(self.rows) + 1, user_id=user_id, created_at=None,
                               result=SimpleNamespace(**result), heatmap=SimpleNamespace(heatmap_path=heatmap_path))
        self.rows.append(case)
        return case

    def list_for_user(self, user_id): return [c for c in self.rows if c.user_id == user_id]

    def get_for_user(self, case_id, user_id):
        for c in self.rows:
            if c.id == case_id and c.user_id == user_id:
                return c
        raise NotFound("Case not found.")


def service(probabilities, ready=True, validator=None):
    return ScreeningService(validator or ImageValidator([FileTypeCheck()]), FakeClassifier(probabilities, ready),
                            FakeExplainer(), FakeStore(), FakeCases(), model_version="test-model")


CONFIDENT_NEVUS = [0, 0, 0, 0, 0, 1.0, 0]
UNSURE_WITH_MELANOMA = [0.1, 0.1, 0.1, 0.05, 0.35, 0.25, 0.05]
IMAGE = jpeg_bytes(textured_image())


# ---------- screening ----------
def test_confident_benign_result():
    r = service(CONFIDENT_NEVUS).screen(user_id=1, content_type="image/jpeg", data=IMAGE)
    assert (r.predicted_class, r.class_name, r.review_recommended) == ("nv", "Nevus", False)
    assert r.probabilities["nv"] == 1.0 and r.model_version == "test-model"
    assert base64.b64decode(r.heatmap_base64) == b"PNG-heatmap-for-5"


def test_unsure_melanoma_result_is_flagged_with_both_reasons():
    r = service(UNSURE_WITH_MELANOMA).screen(1, "image/jpeg", IMAGE)
    assert r.predicted_class == "mel" and r.review_recommended
    assert "High uncertainty" in r.review_reason and "Melanoma probability" in r.review_reason


def test_bad_upload_is_rejected_before_the_model_runs():
    with pytest.raises(ImageRejected):
        service(CONFIDENT_NEVUS).screen(1, "text/plain", b"hello")


def test_missing_model_gives_model_not_ready():
    with pytest.raises(ModelNotReady):
        service(CONFIDENT_NEVUS, ready=False).screen(1, "image/jpeg", IMAGE)


def test_saved_case_can_be_listed_and_reopened_only_by_its_owner():
    s = service(UNSURE_WITH_MELANOMA)
    r = s.screen(user_id=7, content_type="image/jpeg", data=IMAGE)
    assert [c.case_id for c in s.list_cases(7)] == [r.case_id] and s.list_cases(8) == []
    again = s.get_case(user_id=7, case_id=r.case_id)
    assert again.predicted_class == r.predicted_class and again.heatmap_base64 == r.heatmap_base64
    with pytest.raises(NotFound):
        s.get_case(user_id=8, case_id=r.case_id)


# ---------- authentication ----------
class FakeUsers:
    def __init__(self): self.by_email = {}

    def get(self, user_id): return next((u for u in self.by_email.values() if u.id == user_id), None)

    def get_by_email(self, email): return self.by_email.get(email)

    def add(self, email, password_hash):
        user = SimpleNamespace(id=len(self.by_email) + 1, email=email, password_hash=password_hash)
        self.by_email[email] = user
        return user


@pytest.fixture
def auth():
    return AuthService(FakeUsers(), PasswordHasher(), TokenService("k" * 40, 5))


def test_register_normalises_email_and_login_works(auth):
    token = auth.register("  Elvis@Example.COM ", "password123")
    assert auth.authenticate(token).email == "elvis@example.com"
    assert auth.authenticate(auth.login("elvis@example.com", "password123")).email == "elvis@example.com"


def test_register_rules(auth):
    with pytest.raises(InvalidInput):
        auth.register("no-at-sign", "password123")
    with pytest.raises(InvalidInput):
        auth.register("a@b.c", "short")
    auth.register("a@b.c", "password123")
    with pytest.raises(Conflict):
        auth.register("A@B.C", "password123")


def test_login_failures_do_not_reveal_which_part_was_wrong(auth):
    auth.register("a@b.c", "password123")
    for email, pw in [("a@b.c", "wrong-password"), ("nobody@b.c", "password123")]:
        with pytest.raises(AuthenticationFailed, match="Incorrect email or password."):
            auth.login(email, pw)
