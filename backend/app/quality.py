"""Upload validation: type, size, resolution, blur. Rejects with a clear message."""
import io

import cv2
import numpy as np
from fastapi import HTTPException
from PIL import Image, UnidentifiedImageError

from .config import settings

ALLOWED_TYPES = {"image/jpeg", "image/png"}


def validate_image(content_type: str | None, data: bytes) -> Image.Image:
    if content_type not in ALLOWED_TYPES:
        raise HTTPException(415, "Unsupported file type. Please upload a JPEG or PNG image.")
    if len(data) > settings.max_upload_mb * 1024 * 1024:
        raise HTTPException(413, f"Image is too large. Maximum size is {settings.max_upload_mb} MB.")
    try:
        img = Image.open(io.BytesIO(data))
        img.load()
        img = img.convert("RGB")
    except (UnidentifiedImageError, OSError):
        raise HTTPException(400, "The file could not be read as an image.")

    w, h = img.size
    if min(w, h) < settings.min_side_px:
        raise HTTPException(
            422,
            f"Image resolution is too low ({w}x{h}). Each side must be at least {settings.min_side_px}px. "
            "Move closer to the lesion and retake the photo.",
        )

    sharpness = sharpness_score(img)
    if sharpness < settings.blur_threshold:
        raise HTTPException(
            422,
            f"Image looks too blurry (sharpness {sharpness:.1f}, needs at least {settings.blur_threshold:.1f}). "
            "Hold the camera steady, ensure good lighting and retake the photo.",
        )
    return img


def sharpness_score(img: Image.Image) -> float:
    """Laplacian variance measured at a fixed size, so it does not depend on camera resolution."""
    gray = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2GRAY)
    h, w = gray.shape
    k = settings.sharpness_side_px / max(h, w)
    gray = cv2.resize(gray, (round(w * k), round(h * k)), interpolation=cv2.INTER_AREA)
    return float(cv2.Laplacian(gray, cv2.CV_64F).var())
