from fastapi import APIRouter, Depends

from ...container import AppContainer
from ..dependencies import get_container

router = APIRouter(tags=["system"])


@router.get("/health")
def health(c: AppContainer = Depends(get_container)):
    return {"status": "ok", "model_loaded": c.classifier.ready, "model_error": c.classifier.error}
