"""Low-memory inference without PyTorch, for small hosting plans (e.g. Render's free 512 MB instance).

Same model, same maths as `EfficientNetClassifier` + `GradCamExplainer`:

* The ONNX graph (`scripts/export_onnx.py`) is the EfficientNet-B3 backbone up to `features[-1]`.
* The head (global average pool -> dropout -> linear) is applied in NumPy. MC Dropout keeps each of the
  1536 pooled features with probability 1-p and scales kept ones by 1/(1-p), exactly like
  `nn.Dropout` in training mode, for `mc_dropout_passes` passes; the softmaxes are averaged.
* Grad-CAM needs no autograd here. After `features[-1]` the network is average pool + linear, so the
  gradient of class score c with respect to activation A_k(i, j) is w[c, k] / (H * W) everywhere. Grad-CAM's
  channel weight (the spatial mean of that gradient) is therefore w[c, k] / (H * W), and the map is
  ReLU(sum_k w[c, k] A_k) up to a positive constant that the min-max scaling removes. This is the CAM
  formula, computed exactly. Resizing, scaling and the colour overlay copy `pytorch_grad_cam`.
"""
import io
import logging
import threading
import traceback
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

from ..core.errors import ModelNotReady
from .base import LesionClassifier, Prediction
from .explainer import Explainer
from .model_config import ModelConfig
from .uncertainty import predictive_entropy

log = logging.getLogger("ml")


def _softmax(z: np.ndarray) -> np.ndarray:
    z = z - z.max(axis=-1, keepdims=True)
    e = np.exp(z)
    return e / e.sum(axis=-1, keepdims=True)


class OnnxClassifier(LesionClassifier):
    def __init__(self, onnx_path: Path, head_path: Path, config_path: Path, threads: int = 1):
        self._onnx_path = Path(onnx_path)
        self._head_path = Path(head_path)
        self._config_path = Path(config_path)
        self._threads = threads
        self._session = None
        self._config: ModelConfig | None = None
        self._error: str | None = None
        self._rng = np.random.default_rng()
        # The explainer reuses the feature maps of the image that was just classified (the backbone is the
        # slow part), so prediction and explanation of one request must not interleave with another.
        self.lock = threading.Lock()
        self._cache: tuple[int, np.ndarray] | None = None

    def load(self) -> None:
        missing = [p.name for p in (self._onnx_path, self._head_path, self._config_path) if not p.exists()]
        if missing:
            self._error = f"Model files not found: {', '.join(missing)}. Run scripts/export_onnx.py."
            log.warning(self._error)
            return
        try:
            import onnxruntime as ort

            opts = ort.SessionOptions()
            opts.intra_op_num_threads = self._threads
            opts.inter_op_num_threads = 1
            self._session = ort.InferenceSession(str(self._onnx_path), opts, providers=["CPUExecutionProvider"])
            head = np.load(self._head_path)
            self._w, self._b = head["weight"], head["bias"]
            self._p = float(head["dropout_p"])
            self._config, self._error = ModelConfig.from_file(self._config_path), None
        except Exception:
            self._session = None
            self._error = "Model failed to load."
            log.error(traceback.format_exc())

    @property
    def ready(self) -> bool:
        return self._session is not None

    @property
    def config(self) -> ModelConfig | None:
        return self._config

    @property
    def error(self) -> str | None:
        return self._error

    @property
    def head_weights(self) -> np.ndarray:
        return self._w

    def _require_ready(self) -> None:
        if not self.ready:
            raise ModelNotReady(f"Model not available: {self._error or 'Model not loaded.'}")

    def preprocess(self, image: Image.Image) -> np.ndarray:
        """Resize straight to input_size (bilinear, as torchvision does for PIL images), scale to [0, 1],
        ImageNet-normalise, NCHW float32."""
        cfg = self._config
        x = np.asarray(image.convert("RGB").resize((cfg.input_size, cfg.input_size), Image.BILINEAR),
                       dtype=np.float32) / 255.0
        x = (x - np.asarray(cfg.mean, np.float32)) / np.asarray(cfg.std, np.float32)
        return x.transpose(2, 0, 1)[None].astype(np.float32)

    def feature_maps(self, image: Image.Image) -> np.ndarray:
        """Activations of `features[-1]` for one image, shape (C, H, W). The last result is cached."""
        self._require_ready()
        key = id(image)
        if self._cache and self._cache[0] == key:
            return self._cache[1]
        maps = self._session.run(None, {"image": self.preprocess(image)})[0][0]
        self._cache = (key, maps)
        return maps

    def predict(self, image: Image.Image) -> Prediction:
        self._require_ready()
        with self.lock:
            pooled = self.feature_maps(image).mean(axis=(1, 2))                      # (C,)
            keep = 1.0 - self._p
            T = self._config.mc_dropout_passes
            masks = (self._rng.random((T, pooled.shape[0])) < keep).astype(np.float32) / keep
            logits = (pooled[None] * masks) @ self._w.T + self._b                   # (T, classes)
            p = _softmax(logits).mean(axis=0)
        return Prediction(probabilities=p, entropy=predictive_entropy(p))


class CamExplainer(Explainer):
    """Exact Grad-CAM for this architecture (see module docstring), for the top predicted class."""

    def __init__(self, classifier: OnnxClassifier):
        self.classifier = classifier

    def explain(self, image: Image.Image, class_index: int) -> bytes:
        size = self.classifier.config.input_size
        with self.classifier.lock:
            maps = self.classifier.feature_maps(image)                                    # (C, H, W)
        cam = np.maximum(np.tensordot(self.classifier.head_weights[class_index], maps, axes=1), 0)
        # pytorch_grad_cam.scale_cam_image: shift to 0, divide by max, resize to the input size
        cam = cam - cam.min()
        cam = cam / (1e-7 + cam.max())
        cam = cv2.resize(cam.astype(np.float32), (size, size))
        # ...then BaseCAM.aggregate_multi_layers clips at 0 and min-max scales once more (no resize)
        cam = np.maximum(cam, 0)
        cam = cam - cam.min()
        cam = cam / (1e-7 + cam.max())
        # pytorch_grad_cam.utils.image.show_cam_on_image (use_rgb=True, JET colour map, image_weight=0.5)
        base = np.asarray(image.convert("RGB").resize((size, size)), dtype=np.float32) / 255.0
        heat = cv2.applyColorMap(np.uint8(255 * cam), cv2.COLORMAP_JET)
        heat = cv2.cvtColor(heat, cv2.COLOR_BGR2RGB).astype(np.float32) / 255.0
        overlay = 0.5 * heat + 0.5 * base
        overlay = np.uint8(255 * overlay / np.max(overlay))
        buf = io.BytesIO()
        Image.fromarray(overlay).save(buf, format="PNG")
        return buf.getvalue()
