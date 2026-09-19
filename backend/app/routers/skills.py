import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db, require_roles
from app.models.user import UserRole
from app.schemas.skill import SkillCreate, SkillOut, SkillUpdate
from app.services.skill_service import SkillService

router = APIRouter(prefix="/api/v1/skills", tags=["skills"])


@router.get("", response_model=list[SkillOut])
def list_skills(db: Session = Depends(get_db), _: object = Depends(get_current_user)):
    return SkillService(db).list_skills()


@router.post("", response_model=SkillOut, status_code=status.HTTP_201_CREATED)
def create_skill(
    payload: SkillCreate,
    db: Session = Depends(get_db),
    _: object = Depends(require_roles(UserRole.ADMIN, UserRole.HR)),
):
    return SkillService(db).create_skill(payload)


@router.put("/{skill_id}", response_model=SkillOut)
def update_skill(
    skill_id: uuid.UUID,
    payload: SkillUpdate,
    db: Session = Depends(get_db),
    _: object = Depends(require_roles(UserRole.ADMIN, UserRole.HR)),
):
    return SkillService(db).update_skill(skill_id, payload)
