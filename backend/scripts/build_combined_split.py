"""Phase 2: build the combined (HAM10000 + ISIC 2019) TRAINING list without leakage. Labels only, no images needed.

Run from the repo root:  python backend/scripts/build_combined_split.py

Design (kept deliberately simple so it can be explained):
  * The HAM10000 validation and test splits are FROZEN and are reused unchanged
    (docs/results/split_val.csv and split_test.csv). The old and new models are scored on the same test images.
  * Training = original HAM10000 train + ISIC 2019 images that are NOT HAM10000 (these come from BCN_20000 and MSK).
  * ISIC 2019 contains all 10,015 HAM10000 images with the SAME image id and lesion id, so removing them by image id
    is exact. We never re-add HAM images from the ISIC list, so HAM labels stay as they are in HAM10000.
  * SCC (squamous cell carcinoma) is dropped: it is not one of our 7 classes (decision by the project author).
"""
import json
import urllib.request
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[2]

# ---------------- one config block ----------------
RESULTS = REPO / "docs" / "results"
S3_BASE = "https://isic-challenge-data.s3.amazonaws.com/2019/"        # official ISIC 2019 challenge bucket
ISIC_FILES = ["ISIC_2019_Training_GroundTruth.csv", "ISIC_2019_Training_Metadata.csv"]
CACHE_DIR = REPO / "data" / "isic2019_meta"                           # "data/" is git-ignored
CLASS_CODES = ["akiec", "bcc", "bkl", "df", "mel", "nv", "vasc"]
ISIC_TO_OURS = {"AK": "akiec", "BCC": "bcc", "BKL": "bkl", "DF": "df", "MEL": "mel", "NV": "nv", "VASC": "vasc"}
DROPPED_ISIC_CLASSES = ["SCC"]                                        # decision: drop SCC
ISIC_CLASS_COLUMNS = list(ISIC_TO_OURS) + DROPPED_ISIC_CLASSES + ["UNK"]


def fetch_isic_files() -> dict:
    """Download the two small label files from the official bucket if they are not cached yet."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    for name in ISIC_FILES:
        if not (CACHE_DIR / name).exists():
            urllib.request.urlretrieve(S3_BASE + name, CACHE_DIR / name)
    return {n: pd.read_csv(CACHE_DIR / n) for n in ISIC_FILES}


def isic_table(files: dict) -> pd.DataFrame:
    """One row per ISIC 2019 training image: image_id, lesion_id, isic_class, source."""
    gt, meta = files[ISIC_FILES[0]], files[ISIC_FILES[1]]
    assert gt["image"].is_unique and (gt[ISIC_CLASS_COLUMNS].sum(axis=1) == 1).all(), "expected exactly one label per image"
    df = gt[["image"]].copy()
    df["isic_class"] = gt[ISIC_CLASS_COLUMNS].idxmax(axis=1)
    df = df.merge(meta[["image", "lesion_id"]], on="image", how="left").rename(columns={"image": "image_id"})
    # Where the source is not obvious from lesion_id (about 8% of images have none), say so honestly.
    df["source"] = df["lesion_id"].str.split("_").str[0].fillna("NO_LESION_ID")
    return df


def build(ham: dict, isic: pd.DataFrame) -> tuple:
    """Return (new_train_table, report). Raises if any leakage check fails."""
    ham_all = pd.concat(ham.values())
    frozen = pd.concat([ham["val"], ham["test"]])

    in_ham = isic["image_id"].isin(ham_all["image_id"])                  # exact duplicates by image id
    extra = isic[~in_ham].copy()
    dropped_scc = extra["isic_class"].isin(DROPPED_ISIC_CLASSES)
    extra = extra[~dropped_scc].copy()
    extra["dx"] = extra["isic_class"].map(ISIC_TO_OURS)
    assert extra["dx"].notna().all()

    # ---- leakage checks (frozen val/test vs new training) ----
    assert not set(extra["image_id"]) & set(frozen["image_id"]), "image leakage into val/test"
    assert not set(extra["lesion_id"].dropna()) & set(frozen["lesion_id"]), "lesion leakage into val/test"
    new_train = pd.concat([ham["train"].assign(source="HAM10000"),
                           extra[["image_id", "lesion_id", "dx", "source"]]], ignore_index=True)
    assert new_train["image_id"].is_unique, "duplicate image ids inside the training set"
    assert not set(new_train["image_id"]) & set(frozen["image_id"])
    assert not set(new_train["lesion_id"].dropna()) & set(frozen["lesion_id"])

    # HAM images that ISIC 2019 labels SCC but HAM10000 labels akiec (kept as HAM10000 says)
    ham_labelled_scc = isic[in_ham & isic["isic_class"].isin(DROPPED_ISIC_CLASSES)]
    report = dict(
        isic2019_images=len(isic),
        removed_as_ham10000_duplicates_by_image_id=int(in_ham.sum()),
        ham_images_labelled_scc_in_isic_but_akiec_in_ham=int(len(ham_labelled_scc)),
        dropped_scc_non_ham=int(dropped_scc.sum()),
        added_from_isic2019=len(extra),
        added_by_source=extra["source"].value_counts().to_dict(),
        added_without_lesion_id=int(extra["lesion_id"].isna().sum()),
        train_before=len(ham["train"]), train_after=len(new_train),
        frozen_val=len(ham["val"]), frozen_test=len(ham["test"]),
    )
    return new_train, report


def count_table(ham_train: pd.DataFrame, new_train: pd.DataFrame) -> pd.DataFrame:
    """Per-class training counts before and after adding ISIC 2019."""
    t = pd.DataFrame({"before": ham_train["dx"].value_counts(), "after": new_train["dx"].value_counts()}).reindex(CLASS_CODES)
    t["added"] = t["after"] - t["before"]
    t["share_after"] = (t["after"] / t["after"].sum()).round(4)
    return t


def main() -> None:
    ham = {n: pd.read_csv(RESULTS / f"split_{n}.csv") for n in ["train", "val", "test"]}
    isic = isic_table(fetch_isic_files())
    new_train, report = build(ham, isic)
    counts = count_table(ham["train"], new_train)
    new_train.to_csv(RESULTS / "split2_train.csv", index=False)
    counts.to_csv(RESULTS / "split2_class_counts.csv")
    (RESULTS / "split2_report.json").write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2)); print(counts)


if __name__ == "__main__":
    main()
