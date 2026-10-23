from fastapi import APIRouter, Depends

from ... import models, schemas
from ...services import ScreeningService
from ..dependencies import current_user, get_screening_service

router = APIRouter(prefix="/cases", tags=["cases"])


@router.get("", response_model=list[schemas.CaseSummary])
def list_cases(user: models.User = Depends(current_user), service: ScreeningService = Depends(get_screening_service)):
    return [schemas.CaseSummary.from_overview(o) for o in service.list_cases(user.id)]


@router.get("/{case_id}", response_model=schemas.PredictionOut)
def get_case(case_id: int, user: models.User = Depends(current_user),
             service: ScreeningService = Depends(get_screening_service)):
    return schemas.PredictionOut.from_result(service.get_case(user.id, case_id))
