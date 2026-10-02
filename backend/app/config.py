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

    cors_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]

    # Upload validation
    max_upload_mb: int = 8
    min_side_px: int = 224
    # Laplacian variance measured at 512 px on the long side. Calibrated on 43 real HAM10000 images
    # (all scored >= 6.9; Gaussian-blurred copies with sigma >= 3 scored <= 5.6). Only catches severe blur.
    blur_threshold: float = 5.0
    sharpness_side_px: int = 512

    model_version: str = "efficientnet_b3-v0"


settings = Settings()
settings.storage_dir.mkdir(parents=True, exist_ok=True)
