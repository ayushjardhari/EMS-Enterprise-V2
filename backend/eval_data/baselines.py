"""Keyword baseline: BM25 over each employee's resume text.

Deliberately simple (lower-casing and stop-word removal only, no stemming or
synonyms) so it behaves like a typical keyword search over resumes. It is the
comparison point for the semantic methods.
"""
import math
import re
from collections import Counter

STOPWORDS = set("""a an and are as at be been by for from has have in is it its of on or our that the their
this to we with who will can need needs looking people engineers using run runs over next into than then them
they you your""".split())


def tokenize(text: str) -> list[str]:
    return [t for t in re.findall(r"[a-z0-9+#]+", text.lower()) if t not in STOPWORDS]


def bm25_rank(query: str, documents: dict[str, str], k1: float = 1.5, b: float = 0.75) -> list[str]:
    """Return document keys ordered by BM25 score (ties broken alphabetically)."""
    tokenized = {key: tokenize(text) for key, text in documents.items()}
    n = len(tokenized)
    avg_len = (sum(len(t) for t in tokenized.values()) / n) or 1.0
    df = Counter(term for toks in tokenized.values() for term in set(toks))
    query_terms = set(tokenize(query))
    scores = {}
    for key, toks in tokenized.items():
        tf = Counter(toks)
        score = 0.0
        for term in query_terms:
            if term not in tf:
                continue
            idf = math.log(1 + (n - df[term] + 0.5) / (df[term] + 0.5))
            score += idf * tf[term] * (k1 + 1) / (tf[term] + k1 * (1 - b + b * len(toks) / avg_len))
        scores[key] = score
    return sorted(scores, key=lambda key: (-scores[key], key))
