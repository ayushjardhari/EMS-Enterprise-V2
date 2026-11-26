import pytest

from app.services import match_scoring as ms
from eval_data.baselines import bm25_rank
from eval_data.metrics import ndcg_at_k, precision_at_k, recall_at_k, reciprocal_rank


def test_mentions_skill_whole_word_only():
    assert ms.mentions_skill("We need React and Node.js experience", "React")
    assert ms.mentions_skill("looking for node.js developers", "Node.js")
    assert not ms.mentions_skill("We use Reactive programming", "React")
    assert not ms.mentions_skill("Java developers wanted", "JavaScript")


def test_skill_relevance_explicit_mention_beats_similarity():
    assert ms.skill_relevance("Need Kubernetes", "Kubernetes", 0.2) == 1.0
    assert ms.skill_relevance("Need clusters", "Kubernetes", 0.35) == 0.35
    assert ms.skill_relevance("x", "Kubernetes", -0.2) == 0.0


def test_semantic_raw_blends_best_and_top3_mean():
    assert ms.semantic_raw([]) == 0.0
    assert ms.semantic_raw([0.5]) == pytest.approx(0.5)
    assert ms.semantic_raw([0.6, 0.3, 0.3, 0.9]) == pytest.approx(0.6 * 0.9 + 0.4 * (0.9 + 0.6 + 0.3) / 3)


def test_skill_scores_use_top_three_weighted_by_proficiency():
    skills = [("A", "EXPERT", 8, 1.0), ("B", "BEGINNER", 1, 1.0), ("C", "ADVANCED", 4, 0.5), ("D", "ADVANCED", 9, 0.0)]
    raw, exp, idx = ms.skill_scores(skills)
    assert idx[0] == 0 and 3 not in idx          # best weighted skill first; zero-relevance skill excluded
    assert raw == pytest.approx((1.0 + 0.5 + 0.45) / 3)
    assert 0 < exp <= 1
    assert ms.skill_scores([]) == (0.0, 0.0, [])


def test_min_max_edge_cases():
    assert ms.min_max({}) == {}
    assert ms.min_max({"a": 0.2, "b": 0.2}) == {"a": 1.0, "b": 1.0}
    assert ms.min_max({"a": 0.0, "b": 0.0}) == {"a": 0.0, "b": 0.0}
    assert ms.min_max({"a": 1.0, "b": 3.0, "c": 2.0}) == {"a": 0.0, "b": 1.0, "c": 0.5}


def test_combine_normalises_weights_and_rejects_zero():
    assert ms.combine(1, 0, 0, 0, (2, 2, 0, 0)) == pytest.approx(0.5)
    with pytest.raises(ValueError):
        ms.combine(1, 1, 1, 1, (0, 0, 0, 0))


def test_ranking_metrics():
    grades = {"A": 2, "B": 1}
    assert precision_at_k(["A", "X", "B"], grades, 3) == pytest.approx(2 / 3)
    assert recall_at_k(["A", "X", "B"], grades, 2) == pytest.approx(0.5)
    assert ndcg_at_k(["A", "B"], grades, 5) == pytest.approx(1.0)
    assert ndcg_at_k(["B", "A"], grades, 5) < 1.0
    assert ndcg_at_k(["X", "Y"], grades, 5) == 0.0
    assert reciprocal_rank(["X", "B"], grades) == 0.5


def test_bm25_prefers_documents_with_query_terms_and_is_literal():
    docs = {"devops": "kubernetes helm clusters terraform", "ml": "pytorch models", "fe": "react css"}
    assert bm25_rank("production kubernetes clusters", docs)[0] == "devops"
    # literal matching: no stemming/synonyms, so "container orchestration" finds nothing here
    ranked = bm25_rank("container orchestration", docs)
    assert ranked == sorted(docs)
