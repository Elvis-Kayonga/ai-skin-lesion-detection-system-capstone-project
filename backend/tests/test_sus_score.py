"""Unit tests for the SUS scoring script (known reference values)."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from sus_score import summarise, sus_score  # noqa: E402


def test_best_possible_answers_score_100():
    assert sus_score([5, 1] * 5) == 100.0


def test_worst_possible_answers_score_0():
    assert sus_score([1, 5] * 5) == 0.0


def test_all_neutral_answers_score_50():
    assert sus_score([3] * 10) == 50.0


def test_invalid_answers_are_rejected():
    with pytest.raises(ValueError):
        sus_score([3] * 9)
    with pytest.raises(ValueError):
        sus_score([6] + [3] * 9)


def test_summary_against_target():
    s = summarise([70.0, 80.0, 60.0])
    assert s["mean"] == 70.0 and s["meets_target"] is True and s["participants"] == 3
