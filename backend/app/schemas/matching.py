import uuid
from typing import Literal

from pydantic import BaseModel, Field

from app.models.employee import AvailabilityStatus


class MatchFilters(BaseModel):
    """Structured constraints applied BEFORE any semantic scoring."""
    availability: list[AvailabilityStatus] | None = None
    department_ids: list[uuid.UUID] | None = None
    job_role_ids: list[uuid.UUID] | None = None
    employee_ids: list[uuid.UUID] | None = Field(default=None, description="Restrict the candidate pool (used for evaluation)")


class MatchWeights(BaseModel):
    """Relative importance of each score component. Normalised to sum to 1."""
    semantic: float = Field(0.5, ge=0)
    skill: float = Field(0.3, ge=0)
    experience: float = Field(0.1, ge=0)
    availability: float = Field(0.1, ge=0)


class MatchRequest(BaseModel):
    requirement: str = Field(min_length=10, max_length=4000)
    top_k: int = Field(10, ge=1, le=50)
    filters: MatchFilters = Field(default_factory=MatchFilters)
    weights: MatchWeights | None = None
    explain: Literal["none", "template", "llm"] = "none"
    explain_top_n: int = Field(3, ge=1, le=5, description="How many top candidates get an explanation")


class EvidenceChunk(BaseModel):
    document_id: uuid.UUID
    section: str
    content: str
    similarity: float


class MatchedSkill(BaseModel):
    name: str
    proficiency: str
    years: float
    relevance: float


class ScoreBreakdown(BaseModel):
    semantic: float
    skill: float
    experience: float
    availability: float


class CandidateExplanation(BaseModel):
    text: str
    source: Literal["llm", "template"]
    model: str | None = None
    fallback_reason: str | None = None


class CandidateMatch(BaseModel):
    rank: int
    employee_id: uuid.UUID
    employee_code: str
    full_name: str
    job_role: str
    department: str
    availability_status: AvailabilityStatus
    score: float
    breakdown: ScoreBreakdown
    matched_skills: list[MatchedSkill]
    evidence: list[EvidenceChunk]
    explanation: CandidateExplanation | None = None


class MatchResponse(BaseModel):
    requirement: str
    candidates_considered: int
    results: list[CandidateMatch]
