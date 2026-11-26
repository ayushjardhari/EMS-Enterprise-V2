"""Ranking metrics. ``ranked`` is a list of names, best first; ``grades`` maps name -> 1 or 2."""
import math


def precision_at_k(ranked: list[str], grades: dict[str, int], k: int) -> float:
    return sum(1 for n in ranked[:k] if grades.get(n, 0) > 0) / k


def recall_at_k(ranked: list[str], grades: dict[str, int], k: int) -> float:
    return sum(1 for n in ranked[:k] if grades.get(n, 0) > 0) / len(grades)


def dcg(gains: list[float]) -> float:
    return sum(g / math.log2(i + 2) for i, g in enumerate(gains))


def ndcg_at_k(ranked: list[str], grades: dict[str, int], k: int) -> float:
    ideal = dcg(sorted(grades.values(), reverse=True)[:k])
    return dcg([grades.get(n, 0) for n in ranked[:k]]) / ideal if ideal else 0.0


def reciprocal_rank(ranked: list[str], grades: dict[str, int]) -> float:
    for i, n in enumerate(ranked, start=1):
        if grades.get(n, 0) > 0:
            return 1.0 / i
    return 0.0
