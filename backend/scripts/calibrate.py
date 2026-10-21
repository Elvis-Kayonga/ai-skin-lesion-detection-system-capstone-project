"""Phase 1: temperature scaling + melanoma threshold, using exported MC Dropout logits (CPU only).

Run from the repo root:
    python backend/scripts/calibrate.py                  # report only, changes nothing
    python backend/scripts/calibrate.py --target 0.90 --write-config   # also update model_config.json

Rules this script follows:
  * Temperature, melanoma threshold and entropy threshold are chosen on the VALIDATION set only.
  * The TEST set is only used to report results.
"""
import argparse
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "backend"))
from app import calibration as cal  # noqa: E402


@dataclass
class Config:
    """Every number used by this script lives here (no magic numbers elsewhere)."""
    results_dir: Path = REPO / "docs" / "results"
    figures_dir: Path = REPO / "docs" / "figures"
    model_config: Path = REPO / "backend" / "model" / "model_config.json"
    targets: tuple = (0.85, 0.90, 0.95)       # melanoma sensitivity targets shown in the table
    target: float = 0.90                       # the one written to model_config.json
    entropy_percentile: float = 80.0           # same recipe as the training notebook
    ece_bins: int = 15
    melanoma_index: int = 4                    # "mel" in the alphabetical class order
    old_entropy_threshold: float = 0.4129127562046051   # values currently in model_config.json
    old_melanoma_threshold: float = 0.05
    class_codes: list = field(default_factory=list)


def load_split(results_dir: Path, name: str) -> dict:
    """Load one exported .npz (logits shape: images x passes x classes)."""
    d = np.load(results_dir / f"mc_logits_{name}.npz")
    return dict(logits=d["logits"], labels=d["labels"], ids=d["image_ids"],
                classes=[str(c) for c in d["class_codes"]], seed=int(d["seed"]), passes=int(d["passes"]))


def melanoma_threshold_for_target(p_mel: np.ndarray, labels: np.ndarray, mel_idx: int, target: float) -> float:
    """Highest threshold that still catches at least `target` of true melanomas (validation only).

    Exact method: sort the melanoma probabilities of the true melanomas, and take the k-th largest where
    k = ceil(target * n_melanoma). Flagging p_mel >= that value catches at least k of them.
    """
    mel_scores = np.sort(p_mel[labels == mel_idx])[::-1]
    k = int(np.ceil(target * len(mel_scores)))
    return float(mel_scores[k - 1])


def melanoma_rule_stats(p_mel: np.ndarray, labels: np.ndarray, mel_idx: int, threshold: float) -> dict:
    """Cost/benefit of the rule 'alert if P(melanoma) >= threshold' on one split."""
    alert, is_mel = p_mel >= threshold, labels == mel_idx
    tp = int((alert & is_mel).sum())
    return dict(threshold=threshold, sensitivity=tp / is_mel.sum(), specificity=float((~alert & ~is_mel).sum() / (~is_mel).sum()),
                alert_rate=float(alert.mean()), precision=tp / max(int(alert.sum()), 1))


def flag_report(probs: np.ndarray, labels: np.ndarray, flag: np.ndarray, mel_idx: int) -> dict:
    """The numbers the capstone reports for the review flag."""
    pred = probs.argmax(1)
    correct, is_mel = pred == labels, labels == mel_idx
    return dict(
        accuracy=float(correct.mean()),
        flag_rate=float(flag.mean()),
        accuracy_unflagged=float(correct[~flag].mean()),
        accuracy_flagged=float(correct[flag].mean()),
        share_of_mistakes_flagged=float(flag[~correct].mean()),
        melanoma_sensitivity_top_class=float(correct[is_mel].mean()),
        melanoma_sensitivity_with_flag=float((correct | flag)[is_mel].mean()),
        melanoma_specificity_top_class=float((pred[~is_mel] != mel_idx).mean()),
        melanoma_specificity_unflagged=float((~flag[~is_mel]).mean()),
    )


def calibration_report(pass_logits: np.ndarray, labels: np.ndarray, temperature: float, bins: int) -> dict:
    """ECE and NLL of the MC-averaged probabilities for a given temperature."""
    p = cal.mc_probabilities(pass_logits, temperature)
    return dict(ece=cal.expected_calibration_error(p, labels, bins), nll=cal.nll(p, labels),
                accuracy=float((p.argmax(1) == labels).mean()))


def save_reliability_diagram(path: Path, probs_before: np.ndarray, probs_after: np.ndarray,
                             labels: np.ndarray, temperature: float, bins: int) -> None:
    """Reliability diagram: bars below the diagonal mean the model is overconfident."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(1, 2, figsize=(10, 4.5), sharey=True)
    for ax, probs, title in [(axes[0], probs_before, "Before (T = 1)"), (axes[1], probs_after, f"After (T = {temperature:.2f})")]:
        b = cal.reliability_bins(probs, labels, bins)
        centres, width = (b["edges"][:-1] + b["edges"][1:]) / 2, 1.0 / bins
        shown = b["count"] > 0
        ax.bar(centres[shown], b["accuracy"][shown], width=width * 0.95, edgecolor="k", label="accuracy in bin")
        ax.plot([0, 1], [0, 1], "k--", label="perfect calibration")
        ece = cal.expected_calibration_error(probs, labels, bins)
        ax.set(title=f"{title}  ECE = {ece:.3f}", xlabel="confidence (top class)", xlim=(0, 1), ylim=(0, 1))
    axes[0].set_ylabel("accuracy")
    axes[0].legend(loc="upper left")
    fig.suptitle("Reliability diagram, TEST set (HAM10000, MC Dropout average)")
    fig.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=150)
    plt.close(fig)


def print_table(title: str, rows: list, columns: list) -> None:
    print(f"\n{title}")
    print(" | ".join(f"{c:>16}" for c in columns))
    for r in rows:
        print(" | ".join(f"{r[c]:>16.4f}" if isinstance(r[c], float) else f"{r[c]:>16}" for c in columns))


def main() -> None:
    cfg = Config()
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--target", type=float, default=cfg.target, help="melanoma sensitivity target (validation)")
    parser.add_argument("--write-config", action="store_true", help="write new fields into model_config.json")
    args = parser.parse_args()

    val, test = load_split(cfg.results_dir, "val"), load_split(cfg.results_dir, "test")
    cfg.class_codes = val["classes"]
    assert cfg.class_codes[cfg.melanoma_index] == "mel", "melanoma_index does not point at 'mel'"
    mel = cfg.melanoma_index
    print(f"loaded: val {val['logits'].shape}, test {test['logits'].shape}, mc seed {val['seed']}, passes {val['passes']}")

    # ---- (a) temperature, fitted on VALIDATION only ----
    T = cal.fit_temperature(val["logits"], val["labels"])
    print(f"\nFitted temperature T = {T:.3f}  (T > 1 softens overconfident probabilities)")

    # ---- (b) calibration before vs after ----
    calib = {name: {when: calibration_report(d["logits"], d["labels"], t, cfg.ece_bins)
                    for when, t in [("before", 1.0), ("after", T)]} for name, d in [("val", val), ("test", test)]}
    print_table("Calibration (before = T 1, after = fitted T)",
                [dict(split=s, when=w, **calib[s][w]) for s in calib for w in ("before", "after")],
                ["split", "when", "ece", "nll", "accuracy"])
    p_val_1, p_val_T = cal.mc_probabilities(val["logits"], 1.0), cal.mc_probabilities(val["logits"], T)
    p_test_1, p_test_T = cal.mc_probabilities(test["logits"], 1.0), cal.mc_probabilities(test["logits"], T)
    save_reliability_diagram(cfg.figures_dir / "reliability_diagram_test.png", p_test_1, p_test_T, test["labels"], T, cfg.ece_bins)

    # ---- (c) melanoma threshold table: chosen on val, cost shown on val and test ----
    rows, thresholds = [], {}
    for tgt in cfg.targets:
        thr = melanoma_threshold_for_target(p_val_T[:, mel], val["labels"], mel, tgt)
        thresholds[tgt] = thr
        v, t = (melanoma_rule_stats(p[:, mel], d["labels"], mel, thr) for p, d in [(p_val_T, val), (p_test_T, test)])
        rows.append(dict(target=tgt, threshold=thr, val_sens=v["sensitivity"], val_spec=v["specificity"], val_alert=v["alert_rate"],
                         val_prec=v["precision"], test_sens=t["sensitivity"], test_spec=t["specificity"],
                         test_alert=t["alert_rate"], test_prec=t["precision"]))
    print_table("Melanoma-only rule 'alert if P(mel) >= threshold' (threshold chosen on val; test is report-only)",
                rows, list(rows[0].keys()))

    # ---- (d) full review flag with the chosen target ----
    chosen_thr = melanoma_threshold_for_target(p_val_T[:, mel], val["labels"], mel, args.target)
    ent_thr = float(np.percentile(cal.entropy(p_val_T), cfg.entropy_percentile))  # val only, same recipe as notebook
    flag_old = cal.review_flags(p_test_1, cfg.old_entropy_threshold, mel, cfg.old_melanoma_threshold)["flag"]
    flag_new = cal.review_flags(p_test_T, ent_thr, mel, chosen_thr)["flag"]
    report = {"old (T=1, old thresholds)": flag_report(p_test_1, test["labels"], flag_old, mel),
              f"new (T={T:.2f}, target {args.target:.0%})": flag_report(p_test_T, test["labels"], flag_new, mel)}
    keys = list(next(iter(report.values())).keys())
    print(f"\nReview flag on TEST   entropy thr: old {cfg.old_entropy_threshold:.4f} -> new {ent_thr:.4f} | "
          f"melanoma thr: old {cfg.old_melanoma_threshold:.4f} -> new {chosen_thr:.4f}")
    for k in keys:
        print(f"  {k:<34}" + "".join(f"{v[k]:>14.4f}" for v in report.values()))
    print("  columns: " + " | ".join(report.keys()))

    # ---- save everything for the docs (numbers come from this run only) ----
    out = dict(temperature=T, mc_seed=val["seed"], mc_passes=val["passes"], n_val=len(val["labels"]), n_test=len(test["labels"]),
               calibration=calib, melanoma_table=rows, chosen_target=args.target,
               thresholds=dict(entropy=ent_thr, entropy_percentile=cfg.entropy_percentile, melanoma=chosen_thr),
               review_flag_test=report)
    (cfg.results_dir / "calibration_results.json").write_text(json.dumps(out, indent=2))
    print(f"\nsaved {cfg.results_dir / 'calibration_results.json'} and the reliability diagram")

    # ---- (e) only touch model_config.json when explicitly asked; existing fields are kept ----
    if args.write_config:
        model_cfg = json.loads(cfg.model_config.read_text())
        model_cfg.update(temperature=T, calibrated_entropy_threshold=ent_thr, calibrated_melanoma_threshold=chosen_thr,
                         calibration=dict(fitted_on="validation", target_melanoma_sensitivity=args.target, mc_seed=val["seed"],
                                          mc_passes=val["passes"], before_after_test=report, ece=calib["test"]))
        cfg.model_config.write_text(json.dumps(model_cfg, indent=2))
        print(f"updated {cfg.model_config} (old fields kept, new fields added)")
    else:
        print("model_config.json NOT changed (use --write-config after you choose a target)")


if __name__ == "__main__":
    main()
