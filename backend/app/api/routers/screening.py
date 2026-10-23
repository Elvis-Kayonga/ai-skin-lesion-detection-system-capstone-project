from fastapi import APIRouter, Depends, File, UploadFile

from ... import models, schemas
from ...services import ScreeningService
from ..dependencies import current_user, get_screening_service

router = APIRouter(tags=["screening"])


@router.post("/predict", response_model=schemas.PredictionOut)
def predict(image: UploadFile = File(...), user: models.User = Depends(current_user),
            service: ScreeningService = Depends(get_screening_service)):
    # A plain (non-async) endpoint: FastAPI runs it in a worker thread, so the heavy model work does not
    # block the server from answering other requests (for example /health) in the meantime.
    result = service.screen(user.id, image.content_type, image.file.read())
    return schemas.PredictionOut.from_result(result)
