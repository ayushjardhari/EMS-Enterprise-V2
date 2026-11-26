"""Evidence-grounded explanations for ranked candidates.

Two ways to explain a candidate:

template  built directly from the match record (skills, scores, availability,
          evidence chunks). Cannot invent facts. Always available.
llm       an LLM writes a short justification from the SAME facts and must cite
          evidence as [E1], [E2]... The answer is checked and discarded in
          favour of the template if it is malformed or cites evidence that
          does not exist.

The LLM never changes scores or ranking; it only explains them.
"""
import logging
import re
from dataclasses import dataclass

from app.schemas.matching import CandidateMatch
from app.services.llm_client import LLMClient, LLMError, LLMRateLimited

logger = logging.getLogger(__name__)

MAX_EVIDENCE_CHARS = 400
MAX_WORDS = 140
CITATION = re.compile(r"\[E(\d+)\]")

SYSTEM_PROMPT = (
    "You write short, factual justifications for staffing recommendations. "
    "Use ONLY the facts and evidence provided. Never invent skills, employers, numbers or dates. "
    "Cite the evidence you rely on as [E1], [E2], ... after the claim it supports. "
    "If the evidence does not support part of the requirement, say so as a gap. "
    "Reply in exactly two parts, 'Strengths:' then 'Gaps:', at most 90 words in total."
)


@dataclass
class Explanation:
    text: str
    source: str                 # "llm" or "template"
    model: str | None = None
    fallback_reason: str | None = None


def _evidence_texts(candidate: CandidateMatch) -> list[str]:
    return [e.content.strip().replace("\n", " ")[:MAX_EVIDENCE_CHARS] for e in candidate.evidence]


def template_explanation(candidate: CandidateMatch) -> str:
    """Deterministic explanation assembled only from stored facts."""
    parts = []
    skills = [s for s in candidate.matched_skills if s.relevance > 0]
    if skills:
        listed = ", ".join(f"{s.name} ({s.proficiency.title()}, {s.years:g} yrs)" for s in skills)
        parts.append(f"Most relevant recorded skills: {listed}.")
    else:
        parts.append("No recorded skills clearly match this requirement.")
    if candidate.evidence:
        best = candidate.evidence[0]
        snippet = best.content.strip().replace("\n", " ")[:200].rstrip()
        parts.append(f"Closest resume evidence ({best.section} section, similarity {best.similarity:.2f}): \"{snippet}\"")
    else:
        parts.append("No resume text matched closely, so this ranking rests on recorded skills only.")
    status = candidate.availability_status.value.replace("_", " ").lower()
    parts.append(f"Availability: {status}. {candidate.job_role}, {candidate.department}.")
    b = candidate.breakdown
    parts.append(f"Scores (0-1): semantic {b.semantic:.2f}, skill {b.skill:.2f}, "
                 f"experience {b.experience:.2f}, availability {b.availability:.2f}; overall {candidate.score:.2f}.")
    return " ".join(parts)


def build_messages(requirement: str, candidate: CandidateMatch) -> list[dict]:
    skills = "; ".join(f"{s.name} ({s.proficiency.lower()}, {s.years:g} years)" for s in candidate.matched_skills) or "none recorded"
    evidence = "\n".join(f"[E{i}] ({e.section}) {t}" for i, (e, t) in
                         enumerate(zip(candidate.evidence, _evidence_texts(candidate)), start=1)) or "(no resume evidence retrieved)"
    user = (
        f"Project requirement:\n{requirement}\n\n"
        f"Candidate: {candidate.full_name}, {candidate.job_role}, {candidate.department}; "
        f"availability {candidate.availability_status.value.replace('_', ' ').lower()}.\n"
        f"Recorded skills (most relevant first): {skills}.\n\n"
        f"Resume evidence:\n{evidence}"
    )
    return [{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": user}]


def validate_llm_text(text: str, evidence_count: int) -> str | None:
    """Return None if the text is acceptable, otherwise the reason it was rejected."""
    if len(text.split()) > MAX_WORDS:
        return "too long"
    cited = {int(n) for n in CITATION.findall(text)}
    if any(n < 1 or n > evidence_count for n in cited):
        return "cites evidence that does not exist"
    if evidence_count and not cited:
        return "no evidence cited"
    if "strengths" not in text.lower():
        return "missing Strengths section"
    return None


class ExplanationService:
    def __init__(self, llm: LLMClient | None = None):
        self.llm = llm or LLMClient()

    def explain(self, requirement: str, candidate: CandidateMatch, use_llm: bool = True) -> Explanation:
        template = template_explanation(candidate)
        if not use_llm:
            return Explanation(text=template, source="template")
        try:
            text = self.llm.chat(build_messages(requirement, candidate), max_tokens=700)
        except LLMError as exc:
            logger.warning("LLM explanation failed for %s: %s", candidate.employee_code, exc)
            return Explanation(text=template, source="template", fallback_reason=str(exc))
        problem = validate_llm_text(text, len(candidate.evidence))
        if problem:
            logger.warning("LLM explanation rejected for %s: %s", candidate.employee_code, problem)
            return Explanation(text=template, source="template", fallback_reason=f"rejected: {problem}")
        return Explanation(text=text, source="llm", model=self.llm.model)

    def explain_top(self, requirement: str, candidates: list[CandidateMatch], mode: str, top_n: int) -> dict:
        """Explain the first ``top_n`` candidates. Returns {employee_id: Explanation}.

        After the first rate-limit error the LLM is not called again for this request,
        so one 429 does not turn into several.
        """
        results, llm_available = {}, mode == "llm" and self.llm.configured
        for candidate in candidates[:top_n]:
            if mode == "llm" and not llm_available:
                reason = "LLM_API_KEY is not set" if not self.llm.configured else "rate limit reached earlier in this request"
                results[candidate.employee_id] = Explanation(template_explanation(candidate), "template", fallback_reason=reason)
                continue
            explanation = self.explain(requirement, candidate, use_llm=(mode == "llm"))
            if explanation.fallback_reason and "rate limit" in explanation.fallback_reason:
                llm_available = False
            results[candidate.employee_id] = explanation
        return results
