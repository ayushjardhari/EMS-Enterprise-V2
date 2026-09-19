import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class JobRoleBase(BaseModel):
    title: str = Field(min_length=1, max_length=150)
    description: str | None = Field(default=None, max_length=500)


class JobRoleCreate(JobRoleBase):
    pass


class JobRoleUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=150)
    description: str | None = Field(default=None, max_length=500)


class JobRoleOut(JobRoleBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
