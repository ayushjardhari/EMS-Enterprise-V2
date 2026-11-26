"""Compare ranking methods on the 16 labelled requirements.

    docker compose exec backend python -m eval_data.evaluate

Methods:
  keyword_bm25     keyword search over resume text (baseline)
  semantic_only    resume-chunk similarity only
  semantic+skill   chunk similarity + skill relevance
  hybrid_full      all four components (default weights, or --w-* overrides)

Candidates are always limited to the EVAL-* employees, so the 100 seeded
employees (who have no resumes) do not distort the comparison.
"""
import argparse

from sqlalchemy.orm import Session

import app.models  # noqa: F401
from app.db.session import SessionLocal
from app.models.employee import Employee
from app.schemas.matching import MatchFilters, MatchRequest, MatchWeights
from app.services.embedding_service import Embedder, get_embedder
from app.services.matching_service import MatchingService
from eval_data.baselines import bm25_rank
from eval_data.metrics import ndcg_at_k, precision_at_k, recall_at_k, reciprocal_rank
from eval_data.requirements import REQUIREMENTS

CODE_PREFIX = "EVAL-"


def run_evaluation(db: Session, embedder: Embedder, hybrid_weights: MatchWeights | None = None) -> dict:
    eval_ids = [e.id for e in db.query(Employee).filter(Employee.employee_code.like(f"{CODE_PREFIX}%")).all()]
    if not eval_ids:
        raise SystemExit("No EVAL-* employees found. Run: python -m eval_data.load_eval_data")
    service = MatchingService(db, embedder=embedder)
    hybrid_weights = hybrid_weights or MatchWeights()
    methods = {
        "semantic_only": MatchWeights(semantic=1, skill=0, experience=0, availability=0),
        "semantic+skill": MatchWeights(semantic=0.5, skill=0.5, experience=0, availability=0),
        "hybrid_full": hybrid_weights,
    }
    rankings: dict[str, dict[str, list[str]]] = {m: {} for m in ["keyword_bm25", *methods]}

    for req in REQUIREMENTS:
        filters = MatchFilters(employee_ids=eval_ids, **{k: v for k, v in req["filters"].items()})
        candidates = service.filter_candidates(filters)
        documents = {e.full_name: " ".join(d.extracted_text or "" for d in e.documents) for e in candidates}
        rankings["keyword_bm25"][req["id"]] = bm25_rank(req["text"], documents)
        for name, weights in methods.items():
            response = service.search(MatchRequest(requirement=req["text"], top_k=50, filters=filters, weights=weights))
            rankings[name][req["id"]] = [r.full_name for r in response.results]

    summary = {}
    for method, per_req in rankings.items():
        rows = [(precision_at_k(per_req[r["id"]], r["relevant"], 3), recall_at_k(per_req[r["id"]], r["relevant"], 5),
                 ndcg_at_k(per_req[r["id"]], r["relevant"], 5), reciprocal_rank(per_req[r["id"]], r["relevant"]))
                for r in REQUIREMENTS]
        summary[method] = [sum(col) / len(rows) for col in zip(*rows)]
    return {"summary": summary, "rankings": rankings}


def print_report(result: dict) -> None:
    print("\n### Mean over %d requirements (higher is better)\n" % len(REQUIREMENTS))
    print("| Method | Precision@3 | Recall@5 | nDCG@5 | MRR |\n|---|---|---|---|---|")
    for method, (p3, r5, n5, mrr) in result["summary"].items():
        print(f"| {method} | {p3:.3f} | {r5:.3f} | {n5:.3f} | {mrr:.3f} |")
    print("\n### Per requirement: top 3 of hybrid_full vs labelled relevant (grade)\n")
    print("| Req | Top 3 returned | Labelled relevant |\n|---|---|---|")
    for req in REQUIREMENTS:
        top3 = ", ".join(result["rankings"]["hybrid_full"][req["id"]][:3])
        labels = ", ".join(f"{n} ({g})" for n, g in sorted(req["relevant"].items(), key=lambda x: -x[1]))
        print(f"| {req['id']} | {top3} | {labels} |")


def main() -> None:
    parser = argparse.ArgumentParser()
    for name, default in (("semantic", 0.5), ("skill", 0.3), ("experience", 0.1), ("availability", 0.1)):
        parser.add_argument(f"--w-{name}", type=float, default=default)
    args = parser.parse_args()
    weights = MatchWeights(semantic=args.w_semantic, skill=args.w_skill,
                           experience=args.w_experience, availability=args.w_availability)
    with SessionLocal() as db:
        print_report(run_evaluation(db, get_embedder(), weights))


if __name__ == "__main__":
    main()
