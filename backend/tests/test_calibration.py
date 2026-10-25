"""Tests for the calibration maths. Run from the repo root:  python -m pytest backend/tests -q"""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import calibrate  # noqa: E402

from app.ml import calibration as cal  # noqa: E402

rng = np.random.default_rng(0)


def test_temperature_is_applied_before_averaging():
    """Scaling each pass then averaging must differ from averaging then scaling."""
    logits = rng.normal(size=(5, 10, 7)) * 3
    T = 2.0
    right = cal.mc_probabilities(logits, T)
    wrong = cal.softmax(logits.mean(axis=1) / T)          # the order we must NOT use
    manual = np.mean([cal.softmax(logits[:, p, :] / T) for p in range(10)], axis=0)
    assert np.allclose(right, manual)
    assert not np.allclose(right, wrong)


def test_temperature_one_changes_nothing_and_rows_sum_to_one():
    logits = rng.normal(size=(4, 10, 7))
    p = cal.mc_probabilities(logits, 1.0)
    assert np.allclose(p.sum(axis=1), 1.0)
    assert np.allclose(p, np.mean([cal.softmax(logits[:, k]) for k in range(10)], axis=0))


def test_fit_temperature_recovers_known_overconfidence():
    """Labels drawn from softmax(z); logits shown to the model are 3*z, so the best T is about 3."""
    z = rng.normal(size=(6000, 1, 7)) * 1.5
    labels = np.array([rng.choice(7, p=p) for p in cal.softmax(z[:, 0, :])])
    T = cal.fit_temperature(np.repeat(z * 3.0, 3, axis=1), labels)
    assert 2.6 < T < 3.4


def test_ece_is_zero_for_perfect_and_large_for_overconfident():
    labels = np.zeros(100, dtype=int)
    sure_and_right = np.tile([1.0, 0, 0], (100, 1))
    assert cal.expected_calibration_error(sure_and_right, labels) < 1e-9
    sure_but_half_wrong = np.tile([1.0, 0, 0], (100, 1))
    labels_half = np.array([0] * 50 + [1] * 50)
    assert abs(cal.expected_calibration_error(sure_but_half_wrong, labels_half) - 0.5) < 1e-9


def test_review_flag_triggers_on_entropy_and_on_melanoma():
    mel = 4
    uniform = np.full((1, 7), 1 / 7)                                       # max entropy, p_mel = 0.14
    confident_nv = np.array([[0, 0, 0, 0, 0.02, 0.98, 0]])                  # low entropy, p_mel low
    mel_alert = np.array([[0, 0, 0, 0, 0.30, 0.70, 0]])                     # p_mel above 0.2
    thr_h = 1.0
    assert cal.review_flags(uniform, thr_h, mel, 0.9)["high_entropy"][0]
    assert not cal.review_flags(confident_nv, thr_h, mel, 0.2)["flag"][0]
    r = cal.review_flags(mel_alert, thr_h, mel, 0.2)
    assert r["high_melanoma"][0] and not r["high_entropy"][0] and r["flag"][0]


def test_melanoma_threshold_reaches_target_on_validation():
    labels = np.array([4] * 20 + [5] * 80)
    p_mel = np.concatenate([np.linspace(0.05, 0.95, 20), np.linspace(0.0, 0.5, 80)])
    for target in (0.85, 0.90, 0.95):
        thr = calibrate.melanoma_threshold_for_target(p_mel, labels, 4, target)
        assert calibrate.melanoma_rule_stats(p_mel, labels, 4, thr)["sensitivity"] >= target


def test_flag_report_counts_flag_as_a_catch():
    """A melanoma predicted as another class but flagged counts only in the 'with flag' sensitivity."""
    probs = np.array([[0, 0, 0, 0, 0.9, 0.1, 0], [0, 0, 0, 0, 0.3, 0.7, 0]])
    labels = np.array([4, 4])
    flag = np.array([False, True])
    r = calibrate.flag_report(probs, labels, flag, 4)
    assert r["melanoma_sensitivity_top_class"] == 0.5
    assert r["melanoma_sensitivity_with_flag"] == 1.0
