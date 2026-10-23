"""Lesion classifiers.

`LesionClassifier` is the interface the rest of the app depends on. `EfficientNetClassifier` is the real
model. Because the service only knows the interface, the model can be swapped (a fine-tuned model, or a
stub in tests) without changing any other code.
"""
import logging
import threading
import traceback
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from PIL import Image
from torchvision import models, transforms

from ..core.errors import ModelNotReady
from .model_config import ModelConfig
from .uncertainty import predictive_entropy

log = logging.getLogger("ml")


@dataclass(frozen=True)
class Prediction:
    probabilities: np.ndarray   # MC-averaged softmax over the classes, sums to 1
    entropy: float

    @property
    def top_index(self) -> int:
        return int(np.argmax(self.probabilities))


class LesionClassifier(ABC):
    """Turns a lesion photo into class probabilities with an uncertainty estimate."""

    @abstractmethod
    def load(self) -> None: ...

    @property
    @abstractmethod
    def ready(self) -> bool: ...

    @property
    @abstractmethod
    def config(self) -> ModelConfig | None: ...

    @property
    @abstractmethod
    def error(self) -> str | None: ...

    @abstractmethod
    def predict(self, image: Image.Image) -> Prediction: ...


class EfficientNetClassifier(LesionClassifier):
    """EfficientNet-B3 with MC Dropout. Mirrors the training notebook exactly:
    resize straight to 300x300 (no crop), ImageNet normalisation, backbone once, classifier T times with
    dropout on, then average the softmax."""

    def __init__(self, weights_path: Path, config_path: Path, device: str = "cpu"):
        self._weights_path = Path(weights_path)
        self._config_path = Path(config_path)
        self._device = torch.device(device)
        self._network: nn.Module | None = None
        self._config: ModelConfig | None = None
        self._transform = None
        self._error: str | None = None
        # One model object is shared by all requests. Prediction switches dropout on and off and Grad-CAM
        # attaches hooks, so two requests at once could corrupt each other: run them one at a time.
        self.lock = threading.Lock()

    # ---------- loading ----------
    def load(self) -> None:
        if not self._config_path.exists() or not self._weights_path.exists():
            self._error = (
                f"Model files not found in {self._weights_path.parent}. Place {self._weights_path.name} and "
                f"{self._config_path.name} (from the Colab run) there."
            )
            log.warning(self._error)
            return
        try:
            cfg = ModelConfig.from_file(self._config_path)
            net = models.efficientnet_b3(weights=None)
            net.classifier[1] = nn.Linear(net.classifier[1].in_features, cfg.num_classes)
            net.load_state_dict(torch.load(self._weights_path, map_location=self._device))
            self._network = net.to(self._device).eval()
            self._transform = transforms.Compose([
                transforms.Resize((cfg.input_size, cfg.input_size)),   # direct resize, no crop
                transforms.ToTensor(),
                transforms.Normalize(cfg.mean, cfg.std),
            ])
            self._config, self._error = cfg, None
        except Exception:
            self._error = "Model failed to load."
            log.error(traceback.format_exc())

    # ---------- state ----------
    @property
    def ready(self) -> bool:
        return self._network is not None

    @property
    def config(self) -> ModelConfig | None:
        return self._config

    @property
    def error(self) -> str | None:
        return self._error

    @property
    def network(self) -> nn.Module:
        self._require_ready()
        return self._network

    def _require_ready(self) -> None:
        if not self.ready:
            raise ModelNotReady(f"Model not available: {self._error or 'Model not loaded.'}")

    # ---------- inference ----------
    def preprocess(self, image: Image.Image) -> torch.Tensor:
        self._require_ready()
        return self._transform(image).unsqueeze(0).to(self._device)

    def predict(self, image: Image.Image) -> Prediction:
        self._require_ready()
        x = self.preprocess(image)
        with self.lock, torch.no_grad():
            net = self._network.eval()
            features = F.adaptive_avg_pool2d(net.features(x), 1).flatten(1)   # backbone once
            net.classifier.train()                                             # dropout ON (classifier only)
            try:
                passes = [F.softmax(net.classifier(features), dim=1) for _ in range(self._config.mc_dropout_passes)]
            finally:
                net.classifier.eval()
        p = torch.stack(passes).mean(0)[0].cpu().numpy()
        return Prediction(probabilities=p, entropy=predictive_entropy(p))
