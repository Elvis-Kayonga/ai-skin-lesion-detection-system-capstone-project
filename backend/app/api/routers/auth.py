"""Account routes: register and log in (both return a JWT access token)."""
from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm

from ... import schemas
from ...services import AuthService
from ..dependencies import get_auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=schemas.Token, status_code=201)
def register(body: schemas.Credentials, auth: AuthService = Depends(get_auth_service)):
    return schemas.Token(access_token=auth.register(body.email, body.password))


@router.post("/login", response_model=schemas.Token)
def login(form: OAuth2PasswordRequestForm = Depends(), auth: AuthService = Depends(get_auth_service)):
    """OAuth2 form login (username = email) so the Swagger 'Authorize' button works."""
    return schemas.Token(access_token=auth.login(form.username, form.password))
