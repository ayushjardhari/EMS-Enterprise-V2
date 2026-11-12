import uuid
from datetime import datetime

from pydantic import BaseModel


class DocumentOut(BaseModel):
    id: uuid.UUID
    employee_id: uuid.UUID
    filename: str
    file_type: str
    uploaded_at: datetime
    extraction_status: str
    indexing_status: str = "NOT_INDEXED"

    class Config:
        from_attributes = True


class DocumentDownloadUrl(BaseModel):
    url: str
    expires_in_seconds: int
