import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db, require_roles
from app.models.user import User, UserRole
from app.schemas.document import DocumentDownloadUrl, DocumentOut
from app.services.document_service import DocumentService

router = APIRouter(prefix="/api/v1/documents", tags=["documents"])


@router.get("/employee/{employee_id}", response_model=list[DocumentOut])
def list_documents(employee_id: uuid.UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return DocumentService(db).list_documents(employee_id, user)


@router.get("/{document_id}/download", response_model=DocumentDownloadUrl)
def get_download_url(document_id: uuid.UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return {"url": DocumentService(db).get_download_url(document_id, user), "expires_in_seconds": 900}


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(
    document_id: uuid.UUID,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.ADMIN, UserRole.HR)),
):
    DocumentService(db).delete_document(document_id)
