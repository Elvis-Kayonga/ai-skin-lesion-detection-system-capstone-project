"""Repositories: the only place that talks to the database.

Services ask for "the cases of user 5" instead of writing queries, so the storage could move from SQLite to
PostgreSQL (or anything else) without touching the business code.
"""
from sqlalchemy.orm import Session

from . import models
from .core.errors import NotFound


class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def get(self, user_id: int) -> models.User | None:
        return self.db.get(models.User, user_id)

    def get_by_email(self, email: str) -> models.User | None:
        return self.db.query(models.User).filter_by(email=email).first()

    def add(self, email: str, password_hash: str) -> models.User:
        user = models.User(email=email, password_hash=password_hash)
        self.db.add(user)
        self.db.commit()
        return user


class CaseRepository:
    def __init__(self, db: Session):
        self.db = db

    def add(self, user_id: int, image_path: str, result: dict, heatmap_path: str) -> models.Case:
        case = models.Case(user_id=user_id, image_path=image_path)
        case.result = models.ClassificationResult(**result)
        case.heatmap = models.ExplainabilityMap(heatmap_path=heatmap_path)
        self.db.add(case)
        self.db.commit()
        return case

    def list_for_user(self, user_id: int) -> list[models.Case]:
        cases = (self.db.query(models.Case).filter_by(user_id=user_id)
                 .order_by(models.Case.created_at.desc()).all())
        return [c for c in cases if c.result]

    def get_for_user(self, case_id: int, user_id: int) -> models.Case:
        """A case is only visible to its owner; anyone else gets the same 'not found' as a missing case."""
        case = self.db.get(models.Case, case_id)
        if not case or case.user_id != user_id:
            raise NotFound("Case not found.")
        return case
