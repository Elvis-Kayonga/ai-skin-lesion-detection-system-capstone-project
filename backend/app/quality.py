"""Upload quality checks (Strategy pattern).

Each rule is a small class with one job. `ImageValidator` runs the rules in order and stops at the first
failure. Adding a new rule (for example a brightness check) means writing one new class, not editing the
existing ones.
"""
import io
from abc import ABC, abstractmethod
from functools import cached_property

import cv2
import numpy as np
from PIL import Image, UnidentifiedImageError

from .core.errors import ImageRejected


class Upload:
    """The raw upload plus its decoded image. The image is decoded once, the first time a rule needs it."""

    def __init__(self, content_type: str | None, data: bytes):
        self.content_type = content_type
        self.data = data

    @cached_property
    def image(self) -> Image.Image:
        try:
            img = Image.open(io.BytesIO(self.data))
            img.load()
            return img.convert("RGB")
        except (UnidentifiedImageError, OSError):
            raise ImageRejected("The file could not be read as an image.", status_code=400)


class QualityCheck(ABC):
    """One quality rule. Raise ImageRejected when the upload breaks the rule."""

    @abstractmethod
    def check(self, upload: Upload) -> None: ...


class FileTypeCheck(QualityCheck):
    def __init__(self, allowed: tuple[str, ...] = ("image/jpeg", "image/png")):
        self.allowed = set(allowed)

    def check(self, upload: Upload) -> None:
        if upload.content_type not in self.allowed:
            raise ImageRejected("Unsupported file type. Please upload a JPEG or PNG image.", status_code=415)


class FileSizeCheck(QualityCheck):
    def __init__(self, max_mb: int):
        self.max_mb = max_mb

    def check(self, upload: Upload) -> None:
        if len(upload.data) > self.max_mb * 1024 * 1024:
            raise ImageRejected(f"Image is too large. Maximum size is {self.max_mb} MB.", status_code=413)


class DecodableCheck(QualityCheck):
    """Fails with 400 when the bytes are not a real image (decoding happens inside `Upload.image`)."""

    def check(self, upload: Upload) -> None:
        upload.image


class ResolutionCheck(QualityCheck):
    def __init__(self, min_side_px: int):
        self.min_side_px = min_side_px

    def check(self, upload: Upload) -> None:
        w, h = upload.image.size
        if min(w, h) < self.min_side_px:
            raise ImageRejected(
                f"Image resolution is too low ({w}x{h}). Each side must be at least {self.min_side_px}px. "
                "Move closer to the lesion and retake the photo."
            )


class BlurCheck(QualityCheck):
    """Sharpness = variance of the Laplacian (an edge detector) on the photo resized to a fixed size,
    so the score does not depend on the camera's resolution. A blurry photo has few edges, so a low variance.
    The threshold was calibrated on 43 real HAM10000 images (see docs)."""

    def __init__(self, threshold: float, side_px: int):
        self.threshold = threshold
        self.side_px = side_px

    def score(self, image: Image.Image) -> float:
        gray = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2GRAY)
        h, w = gray.shape
        k = self.side_px / max(h, w)
        gray = cv2.resize(gray, (round(w * k), round(h * k)), interpolation=cv2.INTER_AREA)
        return float(cv2.Laplacian(gray, cv2.CV_64F).var())

    def check(self, upload: Upload) -> None:
        sharpness = self.score(upload.image)
        if sharpness < self.threshold:
            raise ImageRejected(
                f"Image looks too blurry (sharpness {sharpness:.1f}, needs at least {self.threshold:.1f}). "
                "Hold the camera steady, ensure good lighting and retake the photo."
            )


class ImageValidator:
    """Runs the quality rules in order (cheap byte checks first, image checks after)."""

    def __init__(self, checks: list[QualityCheck]):
        self.checks = list(checks)

    @classmethod
    def from_settings(cls, settings) -> "ImageValidator":
        return cls([
            FileTypeCheck(),
            FileSizeCheck(settings.max_upload_mb),
            DecodableCheck(),
            ResolutionCheck(settings.min_side_px),
            BlurCheck(settings.blur_threshold, settings.sharpness_side_px),
        ])

    def validate(self, content_type: str | None, data: bytes) -> Image.Image:
        upload = Upload(content_type, data)
        for rule in self.checks:
            rule.check(upload)
        return upload.image
