from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.skill import Skill
from app.repositories.skill_repository import SkillRepository
from app.schemas.skill import SkillCreate, SkillUpdate


class SkillService:
    def __init__(self, db: Session):
        self.repo = SkillRepository(db)

    def list_skills(self) -> list[Skill]:
        return self.repo.list_all()

    def get_skill(self, skill_id) -> Skill:
        skill = self.repo.get_by_id(skill_id)
        if skill is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Skill not found")
        return skill

    def create_skill(self, payload: SkillCreate) -> Skill:
        if self.repo.get_by_name(payload.name):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Skill already exists")
        return self.repo.create(Skill(**payload.model_dump()))

    def update_skill(self, skill_id, payload: SkillUpdate) -> Skill:
        skill = self.get_skill(skill_id)
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(skill, field, value)
        return self.repo.update(skill)
