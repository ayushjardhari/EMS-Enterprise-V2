"""Ranks employees for a project requirement.

Pipeline:
 1. Structured filtering (SQL): active employees matching availability /
    department / role / explicit id filters.
 2. Semantic retrieval: embed the requirement, search resume chunks of the
    remaining candidates (pgvector, cosine distance), group chunks by employee.
 3. Skill relevance: compare the requirement with each employee's recorded
    skills (explicit mention, otherwise embedding similarity), weighted by proficiency.
 4. Score, rank, and attach the best evidence chunks per employee.
"""
import uuid
from collections import defaultdict

from sqlalchemy.orm import Session, selectinload

from app.models.employee import Employee, EmploymentStatus
from app.models.employee_skill import EmployeeSkill
from app.repositories.document_chunk_repository import DocumentChunkRepository
from app.schemas.matching import (
    CandidateMatch, EvidenceChunk, MatchedSkill, MatchFilters, MatchRequest, MatchResponse,
    MatchWeights, ScoreBreakdown,
)
from app.services import match_scoring as ms
from app.services.embedding_service import Embedder, get_embedder

EVIDENCE_PER_EMPLOYEE = 3
_skill_vector_cache: dict[tuple[str, str], list[float]] = {}


class MatchingService:
    def __init__(self, db: Session, embedder: Embedder | None = None):
        self.db = db
        self._embedder = embedder
        self.chunk_repo = DocumentChunkRepository(db)

    @property
    def embedder(self) -> Embedder:
        return self._embedder or get_embedder()

    # ---- step 1 ----
    def filter_candidates(self, filters: MatchFilters) -> list[Employee]:
        query = (
            self.db.query(Employee)
            .options(selectinload(Employee.skills).selectinload(EmployeeSkill.skill),
                     selectinload(Employee.job_role), selectinload(Employee.department))
            .filter(Employee.employment_status == EmploymentStatus.ACTIVE)
        )
        if filters.availability:
            query = query.filter(Employee.availability_status.in_(filters.availability))
        if filters.department_ids:
            query = query.filter(Employee.department_id.in_(filters.department_ids))
        if filters.job_role_ids:
            query = query.filter(Employee.job_role_id.in_(filters.job_role_ids))
        if filters.employee_ids:
            query = query.filter(Employee.id.in_(filters.employee_ids))
        return query.order_by(Employee.full_name).all()

    # ---- helpers ----
    def _skill_vectors(self, names: set[str]) -> dict[str, list[float]]:
        model = self.embedder.model_name
        missing = sorted(n for n in names if (model, n) not in _skill_vector_cache)
        if missing:
            for name, vec in zip(missing, self.embedder.embed(missing)):
                _skill_vector_cache[(model, name)] = vec
        return {n: _skill_vector_cache[(model, n)] for n in names}

    # ---- steps 2-4 ----
    def search(self, request: MatchRequest) -> MatchResponse:
        candidates = self.filter_candidates(request.filters)
        if not candidates:
            return MatchResponse(requirement=request.requirement, candidates_considered=0, results=[])

        weights = request.weights or MatchWeights()
        weight_tuple = (weights.semantic, weights.skill, weights.experience, weights.availability)
        query_vec = self.embedder.embed([request.requirement])[0]
        ids = [e.id for e in candidates]

        hits = self.chunk_repo.search_similar(query_vec, limit=max(100, request.top_k * 20), employee_ids=ids)
        by_employee: dict[uuid.UUID, list] = defaultdict(list)
        for hit in hits:
            by_employee[hit.chunk.employee_id].append(hit)

        skill_names = {es.skill.name for e in candidates for es in e.skills}
        vectors = self._skill_vectors(skill_names) if skill_names else {}

        semantic_raw, skill_raw, experience, top_skill_rows = {}, {}, {}, {}
        for e in candidates:
            semantic_raw[e.id] = ms.semantic_raw([h.similarity for h in by_employee.get(e.id, [])])
            rows = [
                (es.skill.name, es.proficiency_level.value, float(es.years_of_experience),
                 ms.skill_relevance(request.requirement, es.skill.name, ms.dot(query_vec, vectors[es.skill.name])))
                for es in e.skills
            ]
            skill_raw[e.id], experience[e.id], top_idx = ms.skill_scores(rows)
            top_skill_rows[e.id] = [rows[i] for i in top_idx]

        semantic_norm, skill_norm = ms.min_max(semantic_raw), ms.min_max(skill_raw)
        scored = []
        for e in candidates:
            availability = ms.AVAILABILITY_SCORE[e.availability_status.value]
            score = ms.combine(semantic_norm[e.id], skill_norm[e.id], experience[e.id], availability, weight_tuple)
            scored.append((score, e, ScoreBreakdown(
                semantic=round(semantic_norm[e.id], 4), skill=round(skill_norm[e.id], 4),
                experience=round(experience[e.id], 4), availability=availability)))
        scored.sort(key=lambda t: (-t[0], t[1].full_name))

        results = []
        for rank, (score, e, breakdown) in enumerate(scored[: request.top_k], start=1):
            evidence = sorted(by_employee.get(e.id, []), key=lambda h: -h.similarity)[:EVIDENCE_PER_EMPLOYEE]
            results.append(CandidateMatch(
                rank=rank, employee_id=e.id, employee_code=e.employee_code, full_name=e.full_name,
                job_role=e.job_role.title, department=e.department.name,
                availability_status=e.availability_status, score=round(score, 4), breakdown=breakdown,
                matched_skills=[MatchedSkill(name=n, proficiency=p, years=y, relevance=round(r, 4))
                                for n, p, y, r in top_skill_rows[e.id]],
                evidence=[EvidenceChunk(document_id=h.chunk.document_id, section=h.chunk.section,
                                        content=h.chunk.content, similarity=round(h.similarity, 4)) for h in evidence],
            ))
        return MatchResponse(requirement=request.requirement, candidates_considered=len(candidates), results=results)
