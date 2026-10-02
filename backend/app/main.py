import uuid
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from . import models, schemas
from .config import settings
from .db import Base, engine, get_db
from .ml import DISCLAIMER, ModelNotReady, b64, skin_model
from .quality import validate_image
from .security import create_token, current_user, hash_password, verify_password


@asynccontextmanager
async def lifespan(app: FastAPI):
    if len(settings.secret_key) < 32:
        raise RuntimeError(
            "SECRET_KEY is missing or too short. Create backend/.env with a random value of at least 32 "
            "characters (see the README, step 'Create your .env')."
        )
    Base.metadata.create_all(engine)
    skin_model.load()
    yield


app = FastAPI(
    title="Skin Lesion Pre-Screening API",
    description=f"Explainable, uncertainty-aware pre-screening prototype. **{DISCLAIMER}**",
    version="0.1.0",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["system"])
def health():
    return {"status": "ok", "model_loaded": skin_model.ready, "model_error": skin_model.error}


@app.post("/auth/register", response_model=schemas.Token, status_code=201, tags=["auth"])
def register(body: schemas.Credentials, db: Session = Depends(get_db)):
    email = body.email.strip().lower()
    if "@" not in email or len(body.password) < 8:
        raise HTTPException(422, "Provide a valid email and a password of at least 8 characters.")
    if db.query(models.User).filter_by(email=email).first():
        raise HTTPException(409, "An account with this email already exists.")
    user = models.User(email=email, password_hash=hash_password(body.password))
    db.add(user)
    db.commit()
    return schemas.Token(access_token=create_token(user.id))


@app.post("/auth/login", response_model=schemas.Token, tags=["auth"])
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """OAuth2 form login (username = email) so the Swagger 'Authorize' button works."""
    user = db.query(models.User).filter_by(email=form.username.strip().lower()).first()
    if not user or not verify_password(form.password, user.password_hash):
        raise HTTPException(401, "Incorrect email or password.")
    return schemas.Token(access_token=create_token(user.id))


@app.post("/predict", response_model=schemas.PredictionOut, tags=["screening"])
async def predict(
    image: UploadFile = File(...),
    user: models.User = Depends(current_user),
    db: Session = Depends(get_db),
):
    data = await image.read()
    img = validate_image(image.content_type, data)
    try:
        out = skin_model.predict(img)
    except ModelNotReady as e:
        raise HTTPException(503, f"Model not available: {e}")

    stem = uuid.uuid4().hex
    img_path = settings.storage_dir / f"{stem}.jpg"
    map_path = settings.storage_dir / f"{stem}_cam.png"
    img.save(img_path, format="JPEG", quality=90)
    map_path.write_bytes(out["heatmap_png"])

    case = models.Case(user_id=user.id, image_path=str(img_path))
    case.result = models.ClassificationResult(
        **{k: out[k] for k in (
            "predicted_class", "class_name", "probabilities", "entropy",
            "review_recommended", "review_reason", "model_version", "inference_ms",
        )}
    )
    case.heatmap = models.ExplainabilityMap(heatmap_path=str(map_path))
    db.add(case)
    db.commit()

    return schemas.PredictionOut(
        case_id=case.id,
        heatmap_base64=b64(out["heatmap_png"]),
        **{k: v for k, v in out.items() if k != "heatmap_png"},
    )


def _case_or_404(db: Session, user: models.User, case_id: int) -> models.Case:
    case = db.get(models.Case, case_id)
    if not case or case.user_id != user.id:
        raise HTTPException(404, "Case not found.")
    return case


@app.get("/cases", response_model=list[schemas.CaseSummary], tags=["cases"])
def list_cases(user: models.User = Depends(current_user), db: Session = Depends(get_db)):
    cases = (
        db.query(models.Case).filter_by(user_id=user.id).order_by(models.Case.created_at.desc()).all()
    )
    return [
        schemas.CaseSummary(
            case_id=c.id, created_at=c.created_at, predicted_class=c.result.predicted_class,
            class_name=c.result.class_name, entropy=c.result.entropy,
            review_recommended=c.result.review_recommended,
        )
        for c in cases if c.result
    ]


@app.get("/cases/{case_id}", response_model=schemas.PredictionOut, tags=["cases"])
def get_case(case_id: int, user: models.User = Depends(current_user), db: Session = Depends(get_db)):
    c = _case_or_404(db, user, case_id)
    r = c.result
    with open(c.heatmap.heatmap_path, "rb") as f:
        heat = b64(f.read())
    return schemas.PredictionOut(
        case_id=c.id, predicted_class=r.predicted_class, class_name=r.class_name,
        probabilities=r.probabilities, entropy=r.entropy,
        entropy_threshold=float(skin_model.cfg["entropy_threshold"]) if skin_model.cfg else 0.0,
        review_recommended=r.review_recommended,
        review_reason=r.review_reason, heatmap_base64=heat, model_version=r.model_version,
        disclaimer=DISCLAIMER, inference_ms=r.inference_ms,
    )
