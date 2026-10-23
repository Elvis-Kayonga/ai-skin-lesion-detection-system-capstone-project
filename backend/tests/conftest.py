"""Shared test setup.

Every test run uses its own temporary database, upload folder and secret key, so tests never touch
the real `skin_screening.db` or `storage/` folder. The environment must be set BEFORE the app is imported,
because the settings are read once at import time.
"""
import io
import os
import sys
import tempfile
from pathlib import Path

import numpy as np
import pytest
from PIL import Image, ImageFilter

BACKEND = Path(__file__).resolve().parents[1]
REPO = BACKEND.parent
TMP = Path(tempfile.mkdtemp(prefix="skin_tests_"))

os.environ["SECRET_KEY"] = "test-secret-key-that-is-long-enough-0123456789"
os.environ["DATABASE_URL"] = f"sqlite:///{(TMP / 'test.db').as_posix()}"
os.environ["STORAGE_DIR"] = str(TMP / "storage")
os.environ["MODEL_DIR"] = str(BACKEND / "model")
sys.path.insert(0, str(BACKEND))

SAMPLE_LESION = REPO / "sample_images" / "ISIC_0030440.jpg"


# ---------- image factories (all generated in memory, no patient data) ----------
def jpeg_bytes(img: Image.Image, quality: int = 92) -> bytes:
    buf = io.BytesIO()
    img.convert("RGB").save(buf, format="JPEG", quality=quality)
    return buf.getvalue()


def png_bytes(img: Image.Image) -> bytes:
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def textured_image(size=(400, 400), seed=0) -> Image.Image:
    """Random texture: sharp enough to pass the blur check."""
    rng = np.random.default_rng(seed)
    return Image.fromarray(rng.integers(0, 255, (size[1], size[0], 3), dtype=np.uint8))


def blurry_image() -> Image.Image:
    return textured_image().filter(ImageFilter.GaussianBlur(14))


@pytest.fixture(scope="session")
def sample_lesion_bytes() -> bytes:
    return SAMPLE_LESION.read_bytes()
