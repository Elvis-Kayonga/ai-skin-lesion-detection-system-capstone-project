"""The model contract produced by the training notebook (`model_config.json`), as a typed object."""
import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ModelConfig:
    input_size: int
    mean: list[float]
    std: list[float]
    class_codes: list[str]
    class_names: list[str]
    mc_dropout_passes: int
    entropy_threshold: float
    melanoma_flag_threshold: float
    melanoma_index: int

    @classmethod
    def from_file(cls, path: Path) -> "ModelConfig":
        cfg = json.loads(Path(path).read_text())
        return cls(
            input_size=int(cfg["input_size"]),
            mean=list(cfg["mean"]),
            std=list(cfg["std"]),
            class_codes=list(cfg["class_codes"]),
            class_names=list(cfg["class_names"]),
            mc_dropout_passes=int(cfg["mc_dropout_passes"]),
            entropy_threshold=float(cfg["entropy_threshold"]),
            melanoma_flag_threshold=float(cfg["melanoma_flag_threshold"]),
            melanoma_index=int(cfg["melanoma_index"]),
        )

    @property
    def num_classes(self) -> int:
        return len(self.class_codes)
