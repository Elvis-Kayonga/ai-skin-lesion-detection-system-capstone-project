"""The classifier contract, kept free of PyTorch so the low-memory (ONNX) deployment never imports it."""
from abc import ABC, abstractmethod
from dataclasses import dataclass

import numpy as np
from PIL import Image

from .model_config import ModelConfig


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
