"""FastAPI dependencies: build per-request services from the app-wide container and a database session."""
from fastapi import Depends, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from .. import models
from ..container import AppContainer
from ..db import get_db
from ..repositories import CaseRepository, UserRepository
from ..services import AuthService, ScreeningService

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_container(request: Request) -> AppContainer:
    return request.app.state.container


def get_auth_service(db: Session = Depends(get_db), c: AppContainer = Depends(get_container)) -> AuthService:
    return AuthService(UserRepository(db), c.hasher, c.tokens)


def get_screening_service(db: Session = Depends(get_db),
                          c: AppContainer = Depends(get_container)) -> ScreeningService:
    return ScreeningService(c.validator, c.classifier, c.explainer, c.store, CaseRepository(db),
                            c.settings.model_version)


def current_user(token: str = Depends(oauth2_scheme), auth: AuthService = Depends(get_auth_service)) -> models.User:
    return auth.authenticate(token)
