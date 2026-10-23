"""The "Review recommended" rule."""
from dataclasses import dataclass

import numpy as np

from .model_config import ModelConfig


@dataclass(frozen=True)
class ReviewDecision:
    recommended: bool
    reason: str


class ReviewPolicy:
    """A clinician must review when the model is unsure OR melanoma is possible.

    Missing a melanoma is the worst error, so the melanoma threshold is deliberately low.
    Both thresholds were chosen on the validation set in the training notebook."""

    NO_TRIGGER = "No review trigger met."

    def __init__(self, entropy_threshold: float, melanoma_threshold: float, melanoma_index: int):
        self.entropy_threshold = entropy_threshold
        self.melanoma_threshold = melanoma_threshold
        self.melanoma_index = melanoma_index

    @classmethod
    def from_config(cls, config: ModelConfig) -> "ReviewPolicy":
        return cls(config.entropy_threshold, config.melanoma_flag_threshold, config.melanoma_index)

    def decide(self, probabilities: np.ndarray, entropy: float) -> ReviewDecision:
        reasons = []
        if entropy >= self.entropy_threshold:
            reasons.append(f"High uncertainty (entropy {entropy:.2f} >= {self.entropy_threshold:.2f})")
        p_mel = float(probabilities[self.melanoma_index])
        if p_mel >= self.melanoma_threshold:
            reasons.append(f"Melanoma probability {p_mel:.0%} >= {self.melanoma_threshold:.0%}")
        return ReviewDecision(bool(reasons), "; ".join(reasons) if reasons else self.NO_TRIGGER)
