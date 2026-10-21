"""Calibration maths shared by the offline script and the API (numpy only, no torch).

Keeping the maths in ONE place means the backend and the calibration script cannot drift apart.
The order of operations is fixed and must never change:

    logits of one MC pass  ->  divide by temperature T  ->  softmax  ->  average over passes
"""
import numpy as np

EPS = 1e-12  # avoids log(0)


def softmax(logits: np.ndarray, axis: int = -1) -> np.ndarray:
    """Numerically stable softmax (subtract the max so exp() cannot overflow)."""
    z = logits - logits.max(axis=axis, keepdims=True)
    e = np.exp(z)
    return e / e.sum(axis=axis, keepdims=True)


def mc_probabilities(pass_logits: np.ndarray, temperature: float = 1.0) -> np.ndarray:
    """Average calibrated softmax over MC Dropout passes.

    pass_logits has shape (n_images, n_passes, n_classes). Temperature is applied to EACH pass
    BEFORE softmax and BEFORE averaging. (Averaging first and scaling after gives a different answer.)
    """
    return softmax(pass_logits / temperature, axis=-1).mean(axis=1)


def entropy(probs: np.ndarray) -> np.ndarray:
    """Shannon entropy (natural log) of each row of probabilities."""
    return -(probs * np.log(probs + EPS)).sum(axis=1)


def nll(probs: np.ndarray, labels: np.ndarray) -> float:
    """Mean negative log-likelihood of the true class (lower is better)."""
    return float(-np.log(probs[np.arange(len(labels)), labels] + EPS).mean())


def fit_temperature(pass_logits: np.ndarray, labels: np.ndarray,
                    t_min: float = 0.25, t_max: float = 8.0, n_grid: int = 200, n_refine: int = 40) -> float:
    """Find the single temperature T that minimises NLL of the MC-averaged probabilities.

    One number is fitted, so a simple search is enough: a coarse log-spaced grid, then a
    golden-section refinement around the best grid point. No scipy needed.
    """
    def loss(t: float) -> float:
        return nll(mc_probabilities(pass_logits, t), labels)

    grid = np.geomspace(t_min, t_max, n_grid)
    best = int(np.argmin([loss(t) for t in grid]))
    lo, hi = grid[max(best - 1, 0)], grid[min(best + 1, n_grid - 1)]
    phi = (np.sqrt(5) - 1) / 2
    for _ in range(n_refine):
        a, b = hi - phi * (hi - lo), lo + phi * (hi - lo)
        if loss(a) < loss(b):
            hi = b
        else:
            lo = a
    return float((lo + hi) / 2)


def reliability_bins(probs: np.ndarray, labels: np.ndarray, n_bins: int = 15) -> dict:
    """Bin images by top-class confidence; compare confidence with actual accuracy per bin."""
    conf, pred = probs.max(axis=1), probs.argmax(axis=1)
    correct = (pred == labels).astype(float)
    edges = np.linspace(0.0, 1.0, n_bins + 1)
    idx = np.clip(np.digitize(conf, edges[1:-1]), 0, n_bins - 1)
    count = np.bincount(idx, minlength=n_bins)
    sums_conf = np.bincount(idx, weights=conf, minlength=n_bins)
    sums_acc = np.bincount(idx, weights=correct, minlength=n_bins)
    safe = np.maximum(count, 1)
    return dict(edges=edges, count=count, mean_conf=sums_conf / safe, accuracy=sums_acc / safe)


def expected_calibration_error(probs: np.ndarray, labels: np.ndarray, n_bins: int = 15) -> float:
    """ECE = weighted average gap between confidence and accuracy over bins (0 = perfectly calibrated)."""
    b = reliability_bins(probs, labels, n_bins)
    weights = b["count"] / b["count"].sum()
    return float((weights * np.abs(b["mean_conf"] - b["accuracy"])).sum())


def review_flags(probs: np.ndarray, entropy_threshold: float, melanoma_index: int,
                 melanoma_threshold: float) -> dict:
    """Review rule used by the app: flag if entropy is high OR melanoma probability is high.

    Returns both reasons separately so the API can explain why an image was flagged.
    """
    high_entropy = entropy(probs) >= entropy_threshold
    high_mel = probs[:, melanoma_index] >= melanoma_threshold
    return dict(high_entropy=high_entropy, high_melanoma=high_mel, flag=high_entropy | high_mel)
