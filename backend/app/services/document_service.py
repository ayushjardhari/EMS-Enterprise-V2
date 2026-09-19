import uuid
from datetime import datetime, timedelta, timezone
from io import BytesIO

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.minio_client import minio_client
from app.models.document import Document
from app.models.user import User, UserRole
from app.repositories.document_repository import DocumentRepository
from app.repositories.employee_repository import EmployeeRepository
from app.services.document_extraction import extract_text

ALLOWED_CONTENT_TYPES = {
    "application/pdf",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "image/png",
    "image/jpeg",
}
EXTRACTABLE_CONTENT_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}
MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024


class DocumentService:
    def __init__(self, db: Session):
        self.repo = DocumentRepository(db)
        self.employee_repo = EmployeeRepository(db)
        self.db = db

    @staticmethod
    def _can_access_employee(user: User, employee_id: uuid.UUID) -> bool:
        return user.user_role != UserRole.EMPLOYEE or user.employee_id == employee_id

    def list_documents(self, employee_id: uuid.UUID, user: User) -> list[Document]:
        if not self._can_access_employee(user, employee_id):
            raise HTTPException(status_code=403, detail="You can only access your own documents")
        if self.employee_repo.get_by_id(employee_id) is None:
            raise HTTPException(status_code=404, detail="Employee not found")
        return self.repo.list_for_employee(employee_id)

    def upload_document(self, employee_id: uuid.UUID, file: UploadFile, user: User) -> Document:
        if not self._can_access_employee(user, employee_id):
            raise HTTPException(status_code=403, detail="You can only upload documents for yourself")
        if self.employee_repo.get_by_id(employee_id) is None:
            raise HTTPException(status_code=404, detail="Employee not found")
        if file.content_type not in ALLOWED_CONTENT_TYPES:
            raise HTTPException(status_code=400, detail=f"Unsupported file type: {file.content_type}")
        contents = file.file.read()
        if len(contents) > MAX_FILE_SIZE_BYTES:
            raise HTTPException(status_code=400, detail="File exceeds 10 MB limit")
        if not file.filename:
            raise HTTPException(status_code=400, detail="Filename is required")

        document_id = uuid.uuid4()
        safe_name = file.filename.replace("/", "_").replace("\\", "_")
        storage_path = f"{employee_id}/{document_id}_{safe_name}"
        minio_client.put_object(
            settings.MINIO_BUCKET_NAME,
            storage_path,
            BytesIO(contents),
            length=len(contents),
            content_type=file.content_type,
        )
        document = Document(
            id=document_id,
            employee_id=employee_id,
            filename=safe_name,
            file_type=file.content_type,
            storage_path=storage_path,
            extraction_status="NOT_PROCESSED",
        )
        try:
            if file.content_type in EXTRACTABLE_CONTENT_TYPES:
                document.extracted_text = extract_text(contents, file.content_type)
                document.extracted_at = datetime.now(timezone.utc)
                document.extraction_status = "COMPLETED"
            else:
                document.extraction_status = "NOT_SUPPORTED"
            return self.repo.create(document)
        except Exception:
            # Never leave an orphaned object when metadata creation/extraction fails.
            minio_client.remove_object(settings.MINIO_BUCKET_NAME, storage_path)
            raise

    def get_download_url(self, document_id: uuid.UUID, user: User) -> str:
        document = self.repo.get_by_id(document_id)
        if document is None:
            raise HTTPException(status_code=404, detail="Document not found")
        if not self._can_access_employee(user, document.employee_id):
            raise HTTPException(status_code=403, detail="You can only download your own documents")
        return minio_client.presigned_get_object(
            settings.MINIO_BUCKET_NAME, document.storage_path, expires=timedelta(minutes=15)
        )

    def delete_document(self, document_id: uuid.UUID) -> None:
        document = self.repo.get_by_id(document_id)
        if document is None:
            raise HTTPException(status_code=404, detail="Document not found")
        minio_client.remove_object(settings.MINIO_BUCKET_NAME, document.storage_path)
        self.repo.delete(document)
