"""Settings read from environment variables or backend/.env (secrets are never hard-coded)."""
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Secrets come from the environment / .env (never committed).
    secret_key: str = "CHANGE-ME-in-.env"
    access_token_minutes: int = 60 * 8
    database_url: str = f"sqlite:///{BASE_DIR / 'skin_screening.db'}"

    model_dir: Path = BASE_DIR / "model"
    weights_file: str = "efficientnet_b3_best.pth"
    config_file: str = "model_config.json"
    storage_dir: Path = BASE_DIR / "storage"
    # Optional: folder with the built web app (frontend/dist). When set, the API also serves the web app,
    # so the whole system runs behind one address (used for the online demo).
    frontend_dir: Path | None = None

    cors_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]

    # Upload validation
    max_upload_mb: int = 8
    min_side_px: int = 224
    # Laplacian variance measured at 512 px on the long side. Calibrated on 43 real HAM10000 images
    # (all scored >= 6.9; Gaussian-blurred copies with sigma >= 3 scored <= 5.6). Only catches severe blur.
    blur_threshold: float = 5.0
    sharpness_side_px: int = 512

    # The deployed model is the dark-skin fine-tune from Phase 4b. The original HAM10000-only model is kept in
    # model/original: set MODEL_DIR=model/original and MODEL_VERSION=efficientnet_b3-v0 to run it instead.
    model_version: str = "efficientnet_b3-v1-darkskin"
    # "cpu" (default, works everywhere) or "cuda" to run the model on an NVIDIA GPU when one is available.
    device: str = "cpu"
    # Run one throw-away prediction at start-up so the first real user does not pay the one-off set-up cost.
    warmup_on_startup: bool = True

    # "torch" (default: PyTorch + pytorch_grad_cam) or "onnx" (no PyTorch, about a quarter of the memory; same
    # model and maths, see app/ml/onnx_runtime.py). The online demo uses "onnx" to fit a 512 MB free instance.
    inference_backend: str = "torch"
    onnx_file: str = "efficientnet_b3_features.onnx"
    head_file: str = "classifier_head.npz"
    # "disk" (default) or "db": keep photos and heatmaps in the database. Use "db" on hosts whose disk is
    # wiped on restart, so the case history keeps working.
    image_store: str = "disk"


settings = Settings()
settings.storage_dir.mkdir(parents=True, exist_ok=True)
