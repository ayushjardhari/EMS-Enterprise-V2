import uuid

from sqlalchemy.orm import Session

from app.models.skill import Skill


class SkillRepository:
    def __init__(self, db: Session):
        self.db = db

    def list_all(self) -> list[Skill]:
        return self.db.query(Skill).order_by(Skill.name).all()

    def get_by_id(self, skill_id: uuid.UUID) -> Skill | None:
        return self.db.get(Skill, skill_id)

    def get_by_name(self, name: str) -> Skill | None:
        return self.db.query(Skill).filter(Skill.name == name).first()

    def create(self, skill: Skill) -> Skill:
        self.db.add(skill)
        self.db.commit()
        self.db.refresh(skill)
        return skill

    def update(self, skill: Skill) -> Skill:
        self.db.commit()
        self.db.refresh(skill)
        return skill
