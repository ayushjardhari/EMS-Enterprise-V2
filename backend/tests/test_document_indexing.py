import uuid

from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.models.employee import Employee
from app.services.document_indexing_service import DocumentIndexingService

DIM = 384


class FakeEmbedder:
    model_name = "fake-model"
    dim = DIM

    def __init__(self, fail=False):
        self.fail = fail

    def embed(self, texts):
        if self.fail:
            raise RuntimeError("boom")
        return [[float(len(t) % 7)] * DIM for t in texts]


def _make_document(db, sample_department, sample_job_role, text):
    from datetime import date
    employee = Employee(
        employee_code=f"EMP-{uuid.uuid4().hex[:6]}", full_name="Test Person",
        email=f"{uuid.uuid4().hex[:8]}@example.com",
        department_id=sample_department.id, job_role_id=sample_job_role.id, joining_date=date.today(),
    )
    db.add(employee); db.flush()
    document = Document(
        employee_id=employee.id, filename="resume.pdf", file_type="application/pdf",
        storage_path=f"{employee.id}/{uuid.uuid4()}_resume.pdf",
        extraction_status="COMPLETED", extracted_text=text,
    )
    db.add(document); db.commit(); db.refresh(document)
    return document


def test_index_document_stores_section_tagged_chunks(db_session, sample_department, sample_job_role):
    document = _make_document(db_session, sample_department, sample_job_role,
                              "Name\n\nSkills\nPython, Docker\n\nExperience\nBuilt APIs")
    count = DocumentIndexingService(db_session, embedder=FakeEmbedder()).index_document(document)
    chunks = db_session.query(DocumentChunk).filter_by(document_id=document.id).order_by(DocumentChunk.chunk_index).all()
    assert count == len(chunks) == 3
    assert [c.section for c in chunks] == ["general", "skills", "experience"]
    assert all(len(c.embedding) == DIM and c.embedding_model == "fake-model" for c in chunks)
    assert document.indexing_status == "INDEXED" and document.indexed_at is not None


def test_reindex_replaces_old_chunks(db_session, sample_department, sample_job_role):
    document = _make_document(db_session, sample_department, sample_job_role, "Skills\nPython")
    service = DocumentIndexingService(db_session, embedder=FakeEmbedder())
    service.index_document(document)
    document.extracted_text = "Skills\nGo\n\nProjects\nCLI tool"
    db_session.commit()
    service.index_document(document)
    assert db_session.query(DocumentChunk).filter_by(document_id=document.id).count() == 2


def test_document_without_text_is_skipped(db_session, sample_department, sample_job_role):
    document = _make_document(db_session, sample_department, sample_job_role, "   ")
    assert DocumentIndexingService(db_session, embedder=FakeEmbedder()).index_document(document) == 0
    assert document.indexing_status == "SKIPPED"


def test_failure_is_recorded_and_keeps_old_chunks(db_session, sample_department, sample_job_role):
    document = _make_document(db_session, sample_department, sample_job_role, "Skills\nPython")
    DocumentIndexingService(db_session, embedder=FakeEmbedder()).index_document(document)
    document.extracted_text = "Skills\nRust"
    db_session.commit()
    DocumentIndexingService(db_session, embedder=FakeEmbedder(fail=True)).index_document_safely(document)
    assert document.indexing_status == "FAILED"
    assert db_session.query(DocumentChunk).filter_by(document_id=document.id).count() == 1
