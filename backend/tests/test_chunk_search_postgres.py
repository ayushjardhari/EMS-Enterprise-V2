"""Vector search against a real PostgreSQL + pgvector database.

Skipped unless TEST_POSTGRES_URL points at a database that has already been
migrated (``alembic upgrade head``), e.g.:

    TEST_POSTGRES_URL=postgresql+psycopg2://ems_admin:pw@localhost:5432/employee_management pytest tests/test_chunk_search_postgres.py
"""
import hashlib
import math
import os
import re
import uuid
from datetime import date

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import app.models  # noqa: F401
from app.models.department import Department
from app.models.document import Document
from app.models.employee import Employee
from app.models.job_role import JobRole
from app.repositories.document_chunk_repository import DocumentChunkRepository
from app.services.document_indexing_service import DocumentIndexingService

POSTGRES_URL = os.environ.get("TEST_POSTGRES_URL")
pytestmark = pytest.mark.skipif(not POSTGRES_URL, reason="TEST_POSTGRES_URL not set")


class HashEmbedder:
    """Deterministic bag-of-words stand-in so the test needs no model download."""
    model_name = "hash-test"
    dim = 384

    def embed(self, texts):
        out = []
        for t in texts:
            v = [0.0] * self.dim
            for w in re.findall(r"[a-z]+", t.lower()):
                v[int(hashlib.md5(w.encode()).hexdigest(), 16) % self.dim] += 1
            n = math.sqrt(sum(x * x for x in v)) or 1.0
            out.append([x / n for x in v])
        return out


def _employee(db, dept, role, name):
    e = Employee(employee_code=f"T-{uuid.uuid4().hex[:6]}", full_name=name, email=f"{uuid.uuid4().hex[:8]}@t.example",
                 department_id=dept.id, job_role_id=role.id, joining_date=date.today())
    db.add(e); db.flush()
    return e


def test_similarity_search_ranks_and_filters():
    engine = create_engine(POSTGRES_URL)
    db = sessionmaker(bind=engine)()
    try:
        dept = Department(name=f"Test-{uuid.uuid4().hex[:6]}"); db.add(dept); db.flush()
        role = JobRole(title=f"Role-{uuid.uuid4().hex[:6]}"); db.add(role); db.flush()
        devops = _employee(db, dept, role, "Devops")
        ml = _employee(db, dept, role, "ML")
        texts = {
            devops: "Skills\nKubernetes, Docker, Terraform\n\nExperience\nManaged kubernetes clusters",
            ml: "Skills\nPython, scikit-learn\n\nExperience\nBuilt forecasting models",
        }
        embedder = HashEmbedder()
        for emp, txt in texts.items():
            doc = Document(employee_id=emp.id, filename="r.pdf", file_type="application/pdf",
                           storage_path=f"{emp.id}/r.pdf", extraction_status="COMPLETED", extracted_text=txt)
            db.add(doc); db.commit(); db.refresh(doc)
            DocumentIndexingService(db, embedder=embedder).index_document(doc)

        repo = DocumentChunkRepository(db)
        query = embedder.embed(["kubernetes clusters docker"])[0]
        hits = repo.search_similar(query, limit=3, employee_ids=[devops.id, ml.id])
        assert hits[0].chunk.employee_id == devops.id
        assert hits[0].similarity > hits[-1].similarity

        only_ml = repo.search_similar(query, limit=3, employee_ids=[ml.id])
        assert {h.chunk.employee_id for h in only_ml} == {ml.id}
    finally:
        db.rollback()
        for emp in (locals().get("devops"), locals().get("ml")):
            if emp is not None:
                db.delete(emp)
        db.commit()
        db.close()
