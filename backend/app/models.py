from datetime import datetime, timezone

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base


def _now():
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
    cases: Mapped[list["Case"]] = relationship(back_populates="user")


class Case(Base):
    __tablename__ = "cases"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    image_path: Mapped[str] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
    user: Mapped[User] = relationship(back_populates="cases")
    result: Mapped["ClassificationResult"] = relationship(back_populates="case", uselist=False)
    heatmap: Mapped["ExplainabilityMap"] = relationship(back_populates="case", uselist=False)


class ClassificationResult(Base):
    __tablename__ = "classification_results"
    id: Mapped[int] = mapped_column(primary_key=True)
    case_id: Mapped[int] = mapped_column(ForeignKey("cases.id"), unique=True)
    predicted_class: Mapped[str] = mapped_column(String(16))
    class_name: Mapped[str] = mapped_column(String(100))
    probabilities: Mapped[dict] = mapped_column(JSON)
    entropy: Mapped[float] = mapped_column(Float)
    review_recommended: Mapped[bool] = mapped_column(Boolean)
    review_reason: Mapped[str] = mapped_column(String(300))
    model_version: Mapped[str] = mapped_column(String(64))
    inference_ms: Mapped[int] = mapped_column(Integer)
    case: Mapped[Case] = relationship(back_populates="result")


class ExplainabilityMap(Base):
    __tablename__ = "explainability_maps"
    id: Mapped[int] = mapped_column(primary_key=True)
    case_id: Mapped[int] = mapped_column(ForeignKey("cases.id"), unique=True)
    heatmap_path: Mapped[str] = mapped_column(String(500))
    case: Mapped[Case] = relationship(back_populates="heatmap")
