"""Composition root: builds every long-lived object once, at startup, from the settings.

Per-request objects (repositories and services, which need a database session) are built by the
dependency functions in `api/dependencies.py` using the parts held here.
"""
from .config import Settings
from .ml.classifier import EfficientNetClassifier, LesionClassifier
from .ml.explainer import Explainer, GradCamExplainer
from .quality import ImageValidator
from .security import PasswordHasher, TokenService
from .storage import ImageStore


class AppContainer:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.validator = ImageValidator.from_settings(settings)
        classifier = EfficientNetClassifier(settings.model_dir / settings.weights_file,
                                            settings.model_dir / settings.config_file)
        self.classifier: LesionClassifier = classifier
        self.explainer: Explainer = GradCamExplainer(classifier)
        self.store = ImageStore(settings.storage_dir)
        self.hasher = PasswordHasher()
        self.tokens = TokenService(settings.secret_key, settings.access_token_minutes)

    def start(self) -> None:
        self.classifier.load()
