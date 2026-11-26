import json
import uuid

import httpx
import pytest

from app.models.employee import AvailabilityStatus
from app.schemas.matching import CandidateMatch, EvidenceChunk, MatchedSkill, ScoreBreakdown
from app.services.explanation_service import (
    ExplanationService, build_messages, template_explanation, validate_llm_text,
)
from app.services.llm_client import LLMClient, LLMError, LLMRateLimited


def candidate(evidence=True, name="Rohit Sethi"):
    return CandidateMatch(
        rank=1, employee_id=uuid.uuid4(), employee_code="EVAL-001", full_name=name, job_role="DevOps Engineer",
        department="Engineering", availability_status=AvailabilityStatus.AVAILABLE, score=0.91,
        breakdown=ScoreBreakdown(semantic=1.0, skill=0.8, experience=0.7, availability=1.0),
        matched_skills=[MatchedSkill(name="Kubernetes", proficiency="EXPERT", years=5, relevance=0.4)],
        evidence=[EvidenceChunk(document_id=uuid.uuid4(), section="experience", similarity=0.62,
                                content="Operate 40+ microservices on EKS clusters with ArgoCD.")] * (2 if evidence else 0)
        if evidence else [],
    )


def client(handler, key="k"):
    return LLMClient(base_url="https://llm.example/v1", api_key=key, model="m", transport=httpx.MockTransport(handler))


def ok(text):
    return lambda request: httpx.Response(200, json={"choices": [{"message": {"content": text}}]})


GOOD = "Strengths: runs production workloads on EKS clusters [E1]. Gaps: no Terraform evidence shown."


# ---- LLM client ----
def test_client_success_sends_auth_and_model():
    seen = {}

    def handler(request):
        seen["auth"] = request.headers["authorization"]
        seen["body"] = json.loads(request.content)
        return httpx.Response(200, json={"choices": [{"message": {"content": " hello "}}]})

    assert client(handler).chat([{"role": "user", "content": "hi"}]) == "hello"
    assert seen["auth"] == "Bearer k" and seen["body"]["model"] == "m"


def test_client_errors_become_llm_errors():
    with pytest.raises(LLMError, match="not set"):
        client(ok("x"), key="").chat([])
    with pytest.raises(LLMRateLimited):
        client(lambda r: httpx.Response(429, text="slow down")).chat([])
    with pytest.raises(LLMError, match="HTTP 500") as info:
        client(lambda r: httpx.Response(500, text="secret details")).chat([])
    assert "secret details" not in str(info.value)
    with pytest.raises(LLMError, match="unexpected"):
        client(lambda r: httpx.Response(200, json={"nope": 1})).chat([])
    with pytest.raises(LLMError, match="empty"):
        client(ok("   ")).chat([])

    def boom(request):
        raise httpx.ConnectError("down")

    with pytest.raises(LLMError, match="network"):
        client(boom).chat([])


# ---- template + prompt ----
def test_template_uses_only_record_facts():
    text = template_explanation(candidate())
    assert "Kubernetes (Expert, 5 yrs)" in text and "experience section" in text
    assert "available" in text and "DevOps Engineer" in text and "0.91" in text
    assert "resume evidence" not in template_explanation(candidate(evidence=False)).lower().replace("no resume text", "")


def test_prompt_numbers_evidence_and_forbids_invention():
    messages = build_messages("Need Kubernetes", candidate())
    assert "[E1]" in messages[1]["content"] and "[E2]" in messages[1]["content"]
    assert "Never invent" in messages[0]["content"]


# ---- validation ----
def test_validation_rules():
    assert validate_llm_text(GOOD, 2) is None
    assert validate_llm_text("Strengths: great [E5]. Gaps: none.", 2) == "cites evidence that does not exist"
    assert validate_llm_text("Strengths: great. Gaps: none.", 2) == "no evidence cited"
    assert validate_llm_text("Strengths: fine. Gaps: none.", 0) is None        # nothing to cite is fine
    assert validate_llm_text("Great candidate [E1].", 2) == "missing Strengths section"
    assert validate_llm_text("Strengths " + "word " * 200 + "[E1]", 2) == "too long"


# ---- service behaviour ----
def test_llm_explanation_used_when_valid():
    result = ExplanationService(client(ok(GOOD))).explain("req", candidate())
    assert result.source == "llm" and result.model == "m" and result.fallback_reason is None


def test_falls_back_to_template_on_error_and_bad_output():
    failed = ExplanationService(client(lambda r: httpx.Response(500))).explain("req", candidate())
    assert failed.source == "template" and "HTTP 500" in failed.fallback_reason
    bad = ExplanationService(client(ok("Strengths: made up [E9]. Gaps: none."))).explain("req", candidate())
    assert bad.source == "template" and bad.fallback_reason.startswith("rejected")


def test_explain_top_stops_calling_llm_after_rate_limit():
    calls = []

    def handler(request):
        calls.append(1)
        return httpx.Response(429)

    people = [candidate(name=f"P{i}") for i in range(3)]
    out = ExplanationService(client(handler)).explain_top("req", people, mode="llm", top_n=3)
    assert len(calls) == 1
    assert all(e.source == "template" for e in out.values())
    assert any("earlier" in (e.fallback_reason or "") for e in out.values())


def test_explain_top_without_key_never_calls_network():
    def handler(request):
        raise AssertionError("must not be called")

    out = ExplanationService(client(handler, key="")).explain_top("req", [candidate()], mode="llm", top_n=3)
    assert next(iter(out.values())).fallback_reason == "LLM_API_KEY is not set"


def test_explain_top_template_mode_and_top_n_limit():
    people = [candidate(name=f"P{i}") for i in range(4)]
    out = ExplanationService(client(ok(GOOD))).explain_top("req", people, mode="template", top_n=2)
    assert len(out) == 2 and all(e.source == "template" and e.fallback_reason is None for e in out.values())


# ---- endpoint wiring ----
def test_endpoint_attaches_explanations(client, admin_token, monkeypatch):
    from app.schemas.matching import MatchResponse
    import app.routers.matching as router_module

    # A fresh candidate per call, like the real search (which builds new objects each time).
    monkeypatch.setattr(router_module.MatchingService, "search",
                        lambda self, req: MatchResponse(requirement=req.requirement, candidates_considered=1, results=[candidate()]))
    body = {"requirement": "Engineers who run Kubernetes clusters", "top_k": 3, "explain": "template"}
    response = client.post("/api/v1/matching/search", json=body, headers={"Authorization": f"Bearer {admin_token}"})
    assert response.status_code == 200
    explanation = response.json()["results"][0]["explanation"]
    assert explanation["source"] == "template" and "Kubernetes" in explanation["text"]

    none = client.post("/api/v1/matching/search", json={**body, "explain": "none"},
                       headers={"Authorization": f"Bearer {admin_token}"})
    assert none.json()["results"][0]["explanation"] is None
