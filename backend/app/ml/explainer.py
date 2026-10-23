"""Visual explanations of a prediction."""
import io
from abc import ABC, abstractmethod

import numpy as np
from PIL import Image

from .classifier import EfficientNetClassifier


class Explainer(ABC):
    """Produces a PNG heatmap showing which parts of the image drove the prediction."""

    @abstractmethod
    def explain(self, image: Image.Image, class_index: int) -> bytes: ...


class GradCamExplainer(Explainer):
    """Grad-CAM on the last feature block (`features[-1]`), for the top predicted class, in eval mode, fp32.
    The heatmap shows where the model looked. It does not prove the answer is right."""

    def __init__(self, classifier: EfficientNetClassifier):
        self.classifier = classifier

    def explain(self, image: Image.Image, class_index: int) -> bytes:
        from pytorch_grad_cam import GradCAM
        from pytorch_grad_cam.utils.image import show_cam_on_image
        from pytorch_grad_cam.utils.model_targets import ClassifierOutputTarget

        x = self.classifier.preprocess(image).float()
        size = self.classifier.config.input_size
        with self.classifier.lock:
            net = self.classifier.network.eval()
            with GradCAM(model=net, target_layers=[net.features[-1]]) as cam:
                gray = cam(input_tensor=x, targets=[ClassifierOutputTarget(class_index)])[0]
        base = np.asarray(image.resize((size, size)), dtype=np.float32) / 255.0
        overlay = show_cam_on_image(base, gray, use_rgb=True)
        buf = io.BytesIO()
        Image.fromarray(overlay).save(buf, format="PNG")
        return buf.getvalue()
