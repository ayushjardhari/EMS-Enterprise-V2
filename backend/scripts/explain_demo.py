"""Try matching + explanations from the command line (no login token needed).

    docker compose exec backend python -m scripts.explain_demo "We need engineers to run workloads on Kubernetes clusters"
    docker compose exec backend python -m scripts.explain_demo "..." --mode template --top 3

Candidates are limited to the EVAL-* test employees.
"""
import argparse

import app.models  # noqa: F401
from app.db.session import SessionLocal
from app.models.employee import Employee
from app.schemas.matching import MatchFilters, MatchRequest
from app.services.explanation_service import ExplanationService
from app.services.matching_service import MatchingService


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("requirement")
    parser.add_argument("--mode", choices=["template", "llm"], default="llm")
    parser.add_argument("--top", type=int, default=3)
    parser.add_argument("--all-employees", action="store_true", help="do not limit to EVAL-* employees")
    args = parser.parse_args()
    with SessionLocal() as db:
        ids = None if args.all_employees else [e.id for e in db.query(Employee).filter(Employee.employee_code.like("EVAL-%"))]
        response = MatchingService(db).search(MatchRequest(requirement=args.requirement, top_k=args.top,
                                                          filters=MatchFilters(employee_ids=ids)))
        explanations = ExplanationService().explain_top(args.requirement, response.results, args.mode, args.top)
        for r in response.results:
            e = explanations[r.employee_id]
            note = f" (fallback: {e.fallback_reason})" if e.fallback_reason else ""
            print(f"\n#{r.rank} {r.full_name} - {r.job_role} - score {r.score:.2f} - explained by {e.source}{note}")
            print(e.text)


if __name__ == "__main__":
    main()
