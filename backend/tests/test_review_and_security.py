"""Unit tests for the review rule, the uncertainty measure, password hashing and tokens."""
import math

import numpy as np
import pytest

from app.core.errors import AuthenticationFailed
from app.ml.review import ReviewPolicy
from app.ml.uncertainty import predictive_entropy
from app.security import PasswordHasher, TokenService

MEL = 4


def probs(mel: float, rest_top: int = 5) -> np.ndarray:
    p = np.full(7, (1 - mel) * 0.0)
    p[rest_top] = 1 - mel
    p[MEL] += mel
    return p


# ---------- uncertainty ----------
def test_entropy_is_zero_when_certain_and_maximal_when_uniform():
    assert predictive_entropy(np.eye(7)[0]) == pytest.approx(0.0, abs=1e-9)
    assert predictive_entropy(np.full(7, 1 / 7)) == pytest.approx(math.log(7), rel=1e-6)


# ---------- review rule ----------
policy = ReviewPolicy(entropy_threshold=0.4129, melanoma_threshold=0.05, melanoma_index=MEL)


def test_confident_benign_prediction_is_not_flagged():
    d = policy.decide(probs(0.0), entropy=0.01)
    assert not d.recommended and d.reason == ReviewPolicy.NO_TRIGGER


def test_high_uncertainty_triggers_review():
    d = policy.decide(probs(0.0), entropy=0.5)
    assert d.recommended and "High uncertainty" in d.reason


def test_melanoma_probability_at_threshold_triggers_review():
    d = policy.decide(probs(0.05), entropy=0.01)
    assert d.recommended and "Melanoma probability" in d.reason


def test_both_reasons_are_reported():
    d = policy.decide(probs(0.6), entropy=0.9)
    assert "High uncertainty" in d.reason and "Melanoma probability" in d.reason


# ---------- security ----------
def test_passwords_are_salted_hashes_not_plain_text():
    h = PasswordHasher()
    a, b = h.hash("password123"), h.hash("password123")
    assert a != "password123" and a != b                      # salted: same password, different hash
    assert h.verify("password123", a) and not h.verify("wrong", a)


def test_token_round_trip():
    tokens = TokenService("a" * 40, lifetime_minutes=5)
    assert tokens.user_id_from(tokens.issue(42)) == 42


def test_expired_token_is_rejected():
    tokens = TokenService("a" * 40, lifetime_minutes=-1)       # already expired when issued
    with pytest.raises(AuthenticationFailed):
        tokens.user_id_from(tokens.issue(42))


def test_token_signed_with_another_key_is_rejected():
    forged = TokenService("b" * 40, 5).issue(42)
    with pytest.raises(AuthenticationFailed):
        TokenService("a" * 40, 5).user_id_from(forged)
