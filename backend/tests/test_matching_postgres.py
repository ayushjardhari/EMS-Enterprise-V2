"""MatchingService against real PostgreSQL + pgvector (skipped unless TEST_POSTGRES_URL is set).

    TEST_POSTGRES_URL=postgresql+psycopg2://ems_admin:pw@localhost:5432/employee_management pytest tests/test_matching_postgres.py
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
from app.models.employee import AvailabilityStatus, Employee
from app.models.employee_skill import EmployeeSkill, ProficiencyLevel
from app.models.job_role import JobRole
from app.models.skill import Skill
from app.schemas.matching import MatchFilters, MatchRequest
from app.services.document_indexing_service import DocumentIndexingService
from app.services.matching_service import MatchingService

POSTGRES_URL = os.environ.get("TEST_POSTGRES_URL")
pytestmark = pytest.mark.skipif(not POSTGRES_URL, reason="TEST_POSTGRES_URL not set")


class HashEmbedder:
    model_name, dim = "hash-test", 384

    def embed(self, texts):
        out = []
        for t in texts:
            v = [0.0] * self.dim
            for w in re.findall(r"[a-z]+", t.lower()):
                v[int(hashlib.md5(w.encode()).hexdigest(), 16) % self.dim] += 1
            n = math.sqrt(sum(x * x for x in v)) or 1.0
            out.append([x / n for x in v])
        return out


def test_matching_filters_ranks_and_returns_evidence():
    db = sessionmaker(bind=create_engine(POSTGRES_URL))()
    tag = uuid.uuid4().hex[:6]
    created = []
    try:
        dept = Department(name=f"T-{tag}"); role = JobRole(title=f"R-{tag}")
        k8s = Skill(name=f"Kubernetes{tag}", category="DevOps"); torch = Skill(name=f"PyTorch{tag}", category="AI")
        db.add_all([dept, role, k8s, torch]); db.flush()

        def make(name, availability, skill, resume):
            e = Employee(employee_code=f"T{tag}{len(created)}", full_name=name, email=f"{uuid.uuid4().hex[:8]}@t.example",
                         department_id=dept.id, job_role_id=role.id, joining_date=date.today(), availability_status=availability)
            db.add(e); db.flush(); created.append(e)
            db.add(EmployeeSkill(employee_id=e.id, skill_id=skill.id, proficiency_level=ProficiencyLevel.EXPERT, years_of_experience=6))
            if resume:
                d = Document(employee_id=e.id, filename="r.pdf", file_type="application/pdf", storage_path=f"{e.id}/r.pdf",
                             extraction_status="COMPLETED", extracted_text=resume)
                db.add(d); db.commit(); db.refresh(d)
                DocumentIndexingService(db, embedder=HashEmbedder()).index_document(d)
            db.commit()
            return e

        devops = make("Devops", AvailabilityStatus.AVAILABLE, k8s, "Skills\nkubernetes clusters helm\n\nExperience\nran kubernetes clusters in production")
        away = make("Away", AvailabilityStatus.UNAVAILABLE, k8s, "Skills\nkubernetes clusters\n\nExperience\nmanaged kubernetes clusters")
        ml = make("ML", AvailabilityStatus.AVAILABLE, torch, "Skills\npytorch models\n\nExperience\ntrained vision models")
        pool = [e.id for e in created]

        service = MatchingService(db, embedder=HashEmbedder())
        request = MatchRequest(requirement="production kubernetes clusters engineer", top_k=5, filters=MatchFilters(employee_ids=pool))
        response = service.search(request)
        names = [r.full_name for r in response.results]
        assert response.candidates_considered == 3
        assert names[0] == "Devops" and names.index("Devops") < names.index("ML")
        top = response.results[0]
        assert top.evidence and top.evidence[0].similarity >= top.evidence[-1].similarity
        assert top.matched_skills[0].name == k8s.name or top.matched_skills[0].relevance >= 0

        # structured filter removes the unavailable person entirely
        only_available = service.search(MatchRequest(requirement=request.requirement, top_k=5, filters=MatchFilters(
            employee_ids=pool, availability=[AvailabilityStatus.AVAILABLE])))
        assert "Away" not in [r.full_name for r in only_available.results]
        assert only_available.candidates_considered == 2
    finally:
        db.rollback()
        for e in created:
            db.delete(e)
        for obj in (locals().get("k8s"), locals().get("torch"), locals().get("role"), locals().get("dept")):
            if obj is not None:
                db.delete(obj)
        db.commit(); db.close()
