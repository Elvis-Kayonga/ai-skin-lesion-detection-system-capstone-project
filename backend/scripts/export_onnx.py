"""Export the deployed EfficientNet-B3 to ONNX for the low-memory deployment (no PyTorch at runtime).

The ONNX graph returns the output of the last feature block (`features[-1]`), i.e. the activation maps that
Grad-CAM uses. Everything after it (average pool, dropout, linear layer) is tiny and is computed in NumPy by
`OnnxClassifier`, which keeps MC Dropout and exact Grad-CAM possible without autograd.

Usage (from backend/):  python scripts/export_onnx.py [model_dir]
Writes <model_dir>/efficientnet_b3_features.onnx and <model_dir>/classifier_head.npz.
"""
import json
import sys
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
from torchvision import models

model_dir = Path(sys.argv[1] if len(sys.argv) > 1 else "model")
cfg = json.loads((model_dir / "model_config.json").read_text())
net = models.efficientnet_b3(weights=None)
net.classifier[1] = nn.Linear(net.classifier[1].in_features, len(cfg["class_codes"]))
net.load_state_dict(torch.load(model_dir / "efficientnet_b3_best.pth", map_location="cpu"))
net.eval()

size = int(cfg["input_size"])
torch.onnx.export(
    net.features, torch.randn(1, 3, size, size), model_dir / "efficientnet_b3_features.onnx",
    input_names=["image"], output_names=["features"], opset_version=17, dynamo=False,
)
dropout = net.classifier[0]
np.savez(
    model_dir / "classifier_head.npz",
    weight=net.classifier[1].weight.detach().numpy().astype(np.float32),
    bias=net.classifier[1].bias.detach().numpy().astype(np.float32),
    dropout_p=np.float32(dropout.p),
)
print("exported to", model_dir, "dropout p =", dropout.p)
