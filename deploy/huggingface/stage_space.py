"""Copies exactly the files the Hugging Face Space needs into one folder, ready to upload.

Usage (from the repo root):
    python deploy/huggingface/stage_space.py <output folder>
    hf upload <user>/<space-name> <output folder> . --repo-type space

The Space repo gets: Dockerfile, README.md (the Space card), frontend source, backend app code,
requirements.txt and the deployed model. No .env, databases, uploads or node_modules.
"""
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
SKIP = shutil.ignore_patterns("node_modules", "dist", "test-results", "playwright-report", "__pycache__",
                              "*.pyc", ".env*", "e2e", "*.test.js", "*.test.jsx")


def stage(out: Path) -> None:
    if out.exists():
        shutil.rmtree(out)
    (out / "backend" / "model").mkdir(parents=True)
    shutil.copy(HERE / "Dockerfile", out / "Dockerfile")
    shutil.copy(HERE / "SPACE_README.md", out / "README.md")
    shutil.copytree(REPO / "frontend", out / "frontend", ignore=SKIP)
    shutil.copytree(REPO / "backend" / "app", out / "backend" / "app", ignore=SKIP)
    shutil.copy(REPO / "backend" / "requirements.txt", out / "backend" / "requirements.txt")
    for name in ("efficientnet_b3_best.pth", "model_config.json"):
        shutil.copy(REPO / "backend" / "model" / name, out / "backend" / "model" / name)
    files = [p for p in out.rglob("*") if p.is_file()]
    print(f"staged {len(files)} files, {sum(p.stat().st_size for p in files) / 1e6:.1f} MB, in {out}")


if __name__ == "__main__":
    stage(Path(sys.argv[1] if len(sys.argv) > 1 else "space_build").resolve())
