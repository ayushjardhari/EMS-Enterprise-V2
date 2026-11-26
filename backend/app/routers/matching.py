from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import get_db, require_roles
from app.models.user import UserRole
from app.schemas.matching import CandidateExplanation, MatchRequest, MatchResponse
from app.services.explanation_service import ExplanationService
from app.services.matching_service import MatchingService

router = APIRouter(prefix="/api/v1/matching", tags=["matching"])


@router.post("/search", response_model=MatchResponse)
def search_candidates(
    payload: MatchRequest,
    db: Session = Depends(get_db),
    _: object = Depends(require_roles(UserRole.ADMIN, UserRole.HR, UserRole.MANAGER)),
):
    """Rank employees for a natural-language project requirement."""
    response = MatchingService(db).search(payload)
    if payload.explain != "none" and response.results:
        explanations = ExplanationService().explain_top(
            payload.requirement, response.results, mode=payload.explain, top_n=payload.explain_top_n)
        for candidate in response.results:
            found = explanations.get(candidate.employee_id)
            if found:
                candidate.explanation = CandidateExplanation(
                    text=found.text, source=found.source, model=found.model, fallback_reason=found.fallback_reason)
    return response
