"""Uncertainty measure used by the review rule."""
import numpy as np

EPS = 1e-12   # avoids log(0)


def predictive_entropy(probabilities: np.ndarray) -> float:
    """Shannon entropy -sum(p log p) of the MC-averaged probabilities.

    0 means the model is certain; ln(7) = 1.95 is the maximum for 7 classes (all equally likely)."""
    p = np.asarray(probabilities, dtype=np.float64)
    return float(-(p * np.log(p + EPS)).sum())
