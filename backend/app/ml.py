"""Model loading + inference. Mirrors the training notebook and model_config.json exactly."""
import base64
import io
import json
import logging
import time
import traceback

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from PIL import Image
from torchvision import models, transforms

from .config import settings

log = logging.getLogger("ml")

DISCLAIMER = "Decision-support prototype only. Not a diagnosis. Consult a qualified clinician."


class ModelNotReady(RuntimeError):
    pass


class SkinModel:
    def __init__(self):
        self.model = None
        self.cfg = None
        self.error: str | None = None
        self.device = torch.device("cpu")

    def load(self):
        cfg_path = settings.model_dir / settings.config_file
        w_path = settings.model_dir / settings.weights_file
        if not cfg_path.exists() or not w_path.exists():
            self.error = (
                f"Model files not found in {settings.model_dir}. Place {settings.weights_file} and "
                f"{settings.config_file} (from the Colab run) there."
            )
            log.warning(self.error)
            return
        try:
            self.cfg = json.loads(cfg_path.read_text())
            m = models.efficientnet_b3(weights=None)
            m.classifier[1] = nn.Linear(m.classifier[1].in_features, len(self.cfg["class_codes"]))
            m.load_state_dict(torch.load(w_path, map_location=self.device))
            self.model = m.to(self.device).eval()
            self.tf = transforms.Compose([
                transforms.Resize((self.cfg["input_size"], self.cfg["input_size"])),  # direct resize, no crop
                transforms.ToTensor(),
                transforms.Normalize(self.cfg["mean"], self.cfg["std"]),
            ])
            self.error = None
        except Exception:
            self.error = "Model failed to load."
            log.error(traceback.format_exc())

    @property
    def ready(self) -> bool:
        return self.model is not None

    def predict(self, img: Image.Image) -> dict:
        if not self.ready:
            raise ModelNotReady(self.error or "Model not loaded.")
        cfg, t0 = self.cfg, time.perf_counter()
        x = self.tf(img).unsqueeze(0).to(self.device)

        # MC Dropout: backbone once, classifier T times with dropout active.
        self.model.eval()
        with torch.no_grad():
            feats = F.adaptive_avg_pool2d(self.model.features(x), 1).flatten(1)
            self.model.classifier.train()
            probs = torch.stack([
                F.softmax(self.model.classifier(feats), dim=1) for _ in range(cfg["mc_dropout_passes"])
            ]).mean(0)[0]
            self.model.classifier.eval()
        p = probs.cpu().numpy()
        entropy = float(-(p * np.log(p + 1e-12)).sum())
        top = int(p.argmax())

        p_mel = float(p[cfg["melanoma_index"]])
        reasons = []
        if entropy >= cfg["entropy_threshold"]:
            reasons.append(f"High uncertainty (entropy {entropy:.2f} >= {cfg['entropy_threshold']:.2f})")
        if p_mel >= cfg["melanoma_flag_threshold"]:
            reasons.append(f"Melanoma probability {p_mel:.0%} >= {cfg['melanoma_flag_threshold']:.0%}")

        heatmap = self._gradcam(x, img, top)
        return {
            "predicted_class": cfg["class_codes"][top],
            "class_name": cfg["class_names"][top],
            "probabilities": {c: float(v) for c, v in zip(cfg["class_codes"], p)},
            "entropy": entropy,
            "entropy_threshold": float(cfg["entropy_threshold"]),
            "review_recommended": bool(reasons),
            "review_reason": "; ".join(reasons) if reasons else "No review trigger met.",
            "heatmap_png": heatmap,
            "model_version": settings.model_version,
            "disclaimer": DISCLAIMER,
            "inference_ms": int((time.perf_counter() - t0) * 1000),
        }

    def _gradcam(self, x: torch.Tensor, img: Image.Image, target: int) -> bytes:
        """Grad-CAM on features[-1], top class, eval mode, fp32."""
        from pytorch_grad_cam import GradCAM
        from pytorch_grad_cam.utils.image import show_cam_on_image
        from pytorch_grad_cam.utils.model_targets import ClassifierOutputTarget

        self.model.eval()
        with GradCAM(model=self.model, target_layers=[self.model.features[-1]]) as cam:
            gray = cam(input_tensor=x.float(), targets=[ClassifierOutputTarget(target)])[0]
        size = self.cfg["input_size"]
        base = np.asarray(img.resize((size, size)), dtype=np.float32) / 255.0
        overlay = show_cam_on_image(base, gray, use_rgb=True)
        buf = io.BytesIO()
        Image.fromarray(overlay).save(buf, format="PNG")
        return buf.getvalue()


skin_model = SkinModel()


def b64(data: bytes) -> str:
    return base64.b64encode(data).decode()
