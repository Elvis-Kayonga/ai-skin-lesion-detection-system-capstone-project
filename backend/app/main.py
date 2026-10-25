"""App factory: wires the container, routers and the error handler together. No business logic lives here."""
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from .api.routers import auth, cases, screening, system
from .config import Settings, settings
from .container import AppContainer
from .core.constants import DISCLAIMER
from .core.errors import AppError
from .db import Base, engine

MIN_SECRET_LENGTH = 32


def create_app(config: Settings = settings) -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        if len(config.secret_key) < MIN_SECRET_LENGTH:
            raise RuntimeError(
                "SECRET_KEY is missing or too short. Create backend/.env with a random value of at least 32 "
                "characters (see the README, step 'Create your .env')."
            )
        Base.metadata.create_all(engine)
        app.state.container.start()      # loads the model once
        yield

    app = FastAPI(
        title="Skin Lesion Pre-Screening API",
        description=f"Explainable, uncertainty-aware pre-screening prototype. **{DISCLAIMER}**",
        version="0.2.0",
        lifespan=lifespan,
    )
    app.state.container = AppContainer(config)
    app.add_middleware(CORSMiddleware, allow_origins=config.cors_origins, allow_methods=["*"], allow_headers=["*"])

    @app.exception_handler(AppError)
    async def handle_app_error(request: Request, exc: AppError):
        # Same {"detail": "..."} shape FastAPI uses, so clients see one consistent error format.
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})

    for router in (system.router, auth.router, screening.router, cases.router):
        app.include_router(router)
    if config.frontend_dir and config.frontend_dir.is_dir():
        # Mounted last, so every API route above keeps priority over the static files.
        app.mount("/", StaticFiles(directory=config.frontend_dir, html=True), name="web")
    return app


app = create_app()
