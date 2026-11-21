"""The low-memory ONNX backend must give the same answers as the PyTorch model it was exported from."""
import io

import numpy as np
import pytest
from conftest import BACKEND, SAMPLE_LESION
from PIL import Image

ort = pytest.importorskip("onnxruntime")
MODEL = BACKEND / "model"


@pytest.fixture(scope="module")
def onnx_pair():
    from app.ml.onnx_runtime import CamExplainer, OnnxClassifier

    clf = OnnxClassifier(MODEL / "efficientnet_b3_features.onnx", MODEL / "classifier_head.npz",
                         MODEL / "model_config.json")
    clf.load()
    if not clf.ready:
        pytest.skip(clf.error)
    return clf, CamExplainer(clf)


def test_onnx_prediction_is_a_valid_distribution(onnx_pair):
    clf, _ = onnx_pair
    pred = clf.predict(Image.open(SAMPLE_LESION).convert("RGB"))
    assert pred.probabilities.shape == (7,)
    assert pred.probabilities.sum() == pytest.approx(1.0, abs=1e-5)
    assert pred.entropy >= 0


def test_onnx_matches_pytorch(onnx_pair):
    torch = pytest.importorskip("torch")
    from app.ml.classifier import EfficientNetClassifier
    from app.ml.explainer import GradCamExplainer

    clf, cam = onnx_pair
    ref = EfficientNetClassifier(MODEL / "efficientnet_b3_best.pth", MODEL / "model_config.json")
    ref.load()
    image = Image.open(SAMPLE_LESION).convert("RGB")

    with torch.no_grad():   # dropout off: the two backends must agree to float precision
        expected = torch.softmax(ref.network.eval()(ref.preprocess(image)), 1)[0].numpy()
    pooled = clf.feature_maps(image).mean(axis=(1, 2))
    logits = pooled @ clf.head_weights.T + clf._b
    got = np.exp(logits - logits.max())
    got /= got.sum()
    np.testing.assert_allclose(got, expected, atol=1e-5)

    top = int(expected.argmax())
    a = np.asarray(Image.open(io.BytesIO(GradCamExplainer(ref).explain(image, top))), dtype=np.int16)
    b = np.asarray(Image.open(io.BytesIO(cam.explain(image, top))), dtype=np.int16)
    assert a.shape == b.shape
    assert np.abs(a - b).max() <= 4   # rounding only: CAM equals Grad-CAM for this architecture


def test_db_image_store_round_trip():
    from app.db import Base, SessionLocal, engine
    from app.storage import DbImageStore

    Base.metadata.create_all(engine)
    store = DbImageStore(SessionLocal, BACKEND / "storage")
    photo = Image.new("RGB", (2000, 1000), (120, 60, 40))
    image_path, heatmap_path = store.save_case_files(photo, b"\x89PNG-fake")
    assert image_path.startswith("db:") and heatmap_path.startswith("db:")
    assert store.read(heatmap_path) == b"\x89PNG-fake"
    assert max(Image.open(io.BytesIO(store.read(image_path))).size) == DbImageStore.MAX_SIDE
