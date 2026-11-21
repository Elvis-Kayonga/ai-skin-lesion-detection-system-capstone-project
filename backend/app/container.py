"""Composition root: builds every long-lived object once, at startup, from the settings.

Per-request objects (repositories and services, which need a database session) are built by the
dependency functions in `api/dependencies.py` using the parts held here.
"""
import logging
import time

import numpy as np
from PIL import Image

from .config import Settings
from .ml.base import LesionClassifier
from .ml.explainer import Explainer
from .quality import ImageValidator
from .security import PasswordHasher, TokenService
from .storage import DbImageStore, ImageStore


class AppContainer:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.validator = ImageValidator.from_settings(settings)
        self.classifier: LesionClassifier
        self.explainer: Explainer
        if settings.inference_backend == "onnx":
            from .ml.onnx_runtime import CamExplainer, OnnxClassifier

            onnx = OnnxClassifier(settings.model_dir / settings.onnx_file, settings.model_dir / settings.head_file,
                                  settings.model_dir / settings.config_file)
            self.classifier, self.explainer = onnx, CamExplainer(onnx)
        else:   # PyTorch is imported only here, so the ONNX deployment does not need it installed
            from .ml.classifier import EfficientNetClassifier
            from .ml.explainer import GradCamExplainer

            torch_clf = EfficientNetClassifier(settings.model_dir / settings.weights_file,
                                               settings.model_dir / settings.config_file, device=settings.device)
            self.classifier, self.explainer = torch_clf, GradCamExplainer(torch_clf)
        if settings.image_store == "db":
            from .db import SessionLocal

            self.store = DbImageStore(SessionLocal, settings.storage_dir)
        else:
            self.store = ImageStore(settings.storage_dir)
        self.hasher = PasswordHasher()
        self.tokens = TokenService(settings.secret_key, settings.access_token_minutes)

    def start(self) -> None:
        self.classifier.load()
        if self.classifier.ready and self.settings.warmup_on_startup:
            self.warm_up()

    def warm_up(self) -> None:
        """Run one throw-away prediction and heatmap at start-up.

        PyTorch and Grad-CAM do one-off work on their first call (allocating memory, choosing kernels,
        importing the Grad-CAM library). Without this, the first real user waited about 8 seconds instead
        of about 1.4. Doing it here moves that cost into server start-up, before anyone is waiting."""
        started = time.perf_counter()
        size = self.classifier.config.input_size
        noise = np.random.default_rng(0).integers(0, 255, (size, size, 3), dtype=np.uint8)
        image = Image.fromarray(noise)
        prediction = self.classifier.predict(image)
        self.explainer.explain(image, prediction.top_index)
        logging.getLogger("ml").info("model warm-up took %.1f s", time.perf_counter() - started)
