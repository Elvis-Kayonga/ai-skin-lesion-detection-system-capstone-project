"""Business logic. Services receive everything they need in their constructor (dependency injection), so
they can be tested with stubs and do not know about HTTP or SQL details."""
import base64
import time
from dataclasses import dataclass
from datetime import datetime

from . import models
from .core.constants import DISCLAIMER
from .core.errors import AuthenticationFailed, Conflict, InvalidInput
from .ml.classifier import LesionClassifier
from .ml.explainer import Explainer
from .ml.review import ReviewPolicy
from .quality import ImageValidator
from .repositories import CaseRepository, UserRepository
from .security import PasswordHasher, TokenService
from .storage import ImageStore


class AuthService:
    MIN_PASSWORD = 8

    def __init__(self, users: UserRepository, hasher: PasswordHasher, tokens: TokenService):
        self.users = users
        self.hasher = hasher
        self.tokens = tokens

    @staticmethod
    def _normalise(email: str) -> str:
        return email.strip().lower()

    def register(self, email: str, password: str) -> str:
        email = self._normalise(email)
        if "@" not in email or len(password) < self.MIN_PASSWORD:
            raise InvalidInput("Provide a valid email and a password of at least 8 characters.")
        if self.users.get_by_email(email):
            raise Conflict("An account with this email already exists.")
        user = self.users.add(email, self.hasher.hash(password))
        return self.tokens.issue(user.id)

    def login(self, email: str, password: str) -> str:
        user = self.users.get_by_email(self._normalise(email))
        if not user or not self.hasher.verify(password, user.password_hash):
            raise AuthenticationFailed("Incorrect email or password.")
        return self.tokens.issue(user.id)

    def authenticate(self, token: str) -> models.User:
        user = self.users.get(self.tokens.user_id_from(token))
        if not user:
            raise AuthenticationFailed(TokenService.INVALID)
        return user


@dataclass(frozen=True)
class ScreeningResult:
    case_id: int
    predicted_class: str
    class_name: str
    probabilities: dict
    entropy: float
    entropy_threshold: float
    review_recommended: bool
    review_reason: str
    heatmap_base64: str
    model_version: str
    disclaimer: str
    inference_ms: int


@dataclass(frozen=True)
class CaseOverview:
    case_id: int
    created_at: datetime
    predicted_class: str
    class_name: str
    entropy: float
    review_recommended: bool


class ScreeningService:
    """One screening: validate the photo -> classify with uncertainty -> explain -> apply the review rule
    -> save the case. Every step is a separate object, so each can be replaced or tested on its own."""

    def __init__(self, validator: ImageValidator, classifier: LesionClassifier, explainer: Explainer,
                 store: ImageStore, cases: CaseRepository, model_version: str):
        self.validator = validator
        self.classifier = classifier
        self.explainer = explainer
        self.store = store
        self.cases = cases
        self.model_version = model_version

    def screen(self, user_id: int, content_type: str | None, data: bytes) -> ScreeningResult:
        image = self.validator.validate(content_type, data)       # raises ImageRejected with a clear message
        started = time.perf_counter()
        prediction = self.classifier.predict(image)                # raises ModelNotReady if no model
        heatmap = self.explainer.explain(image, prediction.top_index)
        elapsed_ms = int((time.perf_counter() - started) * 1000)

        cfg = self.classifier.config
        decision = ReviewPolicy.from_config(cfg).decide(prediction.probabilities, prediction.entropy)
        top = prediction.top_index
        fields = dict(
            predicted_class=cfg.class_codes[top],
            class_name=cfg.class_names[top],
            probabilities={c: float(v) for c, v in zip(cfg.class_codes, prediction.probabilities, strict=True)},
            entropy=prediction.entropy,
            review_recommended=decision.recommended,
            review_reason=decision.reason,
            model_version=self.model_version,
            inference_ms=elapsed_ms,
        )
        image_path, heatmap_path = self.store.save_case_files(image, heatmap)
        case = self.cases.add(user_id, str(image_path), fields, str(heatmap_path))
        return ScreeningResult(case_id=case.id, entropy_threshold=cfg.entropy_threshold,
                               heatmap_base64=base64.b64encode(heatmap).decode(), disclaimer=DISCLAIMER, **fields)

    def get_case(self, user_id: int, case_id: int) -> ScreeningResult:
        case = self.cases.get_for_user(case_id, user_id)
        r = case.result
        cfg = self.classifier.config
        return ScreeningResult(
            case_id=case.id, predicted_class=r.predicted_class, class_name=r.class_name,
            probabilities=r.probabilities, entropy=r.entropy,
            entropy_threshold=cfg.entropy_threshold if cfg else 0.0,
            review_recommended=r.review_recommended, review_reason=r.review_reason,
            heatmap_base64=base64.b64encode(self.store.read(case.heatmap.heatmap_path)).decode(),
            model_version=r.model_version, disclaimer=DISCLAIMER, inference_ms=r.inference_ms,
        )

    def list_cases(self, user_id: int) -> list[CaseOverview]:
        return [
            CaseOverview(case_id=c.id, created_at=c.created_at, predicted_class=c.result.predicted_class,
                         class_name=c.result.class_name, entropy=c.result.entropy,
                         review_recommended=c.result.review_recommended)
            for c in self.cases.list_for_user(user_id)
        ]
