"""Request and response shapes of the API (what goes over the wire)."""
from dataclasses import asdict
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class Credentials(BaseModel):
    email: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class PredictionOut(BaseModel):
    case_id: int
    predicted_class: str
    class_name: str
    probabilities: dict[str, float]
    entropy: float
    entropy_threshold: float
    review_recommended: bool
    review_reason: str
    heatmap_base64: str
    model_version: str
    disclaimer: str
    inference_ms: int

    @classmethod
    def from_result(cls, result) -> "PredictionOut":
        return cls(**asdict(result))


class CaseSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    case_id: int
    created_at: datetime
    predicted_class: str
    class_name: str
    entropy: float
    review_recommended: bool

    @classmethod
    def from_overview(cls, overview) -> "CaseSummary":
        return cls(**asdict(overview))
