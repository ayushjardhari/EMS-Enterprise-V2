"""Text embeddings via Sentence Transformers.

The model is loaded lazily on first use so that importing the app (and
running the unit tests) does not require PyTorch or a model download.
Vectors are L2-normalised, so cosine distance and inner product agree.
"""
import threading
from typing import Protocol

from app.core.config import settings


class Embedder(Protocol):
    model_name: str
    dim: int

    def embed(self, texts: list[str]) -> list[list[float]]: ...


class SentenceTransformerEmbedder:
    def __init__(self, model_name: str | None = None, batch_size: int = 32):
        self.model_name = model_name or settings.EMBEDDING_MODEL
        self.dim = settings.EMBEDDING_DIM
        self.batch_size = batch_size
        self._model = None
        self._lock = threading.Lock()

    def _load(self):
        if self._model is None:
            with self._lock:
                if self._model is None:
                    from sentence_transformers import SentenceTransformer  # heavy import, kept lazy
                    self._model = SentenceTransformer(self.model_name)
        return self._model

    def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        vectors = self._load().encode(
            texts,
            batch_size=self.batch_size,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        result = [[float(x) for x in vec] for vec in vectors]
        if result and len(result[0]) != self.dim:
            raise ValueError(
                f"Model {self.model_name} returned {len(result[0])}-dim vectors but "
                f"EMBEDDING_DIM / the database column is {self.dim}"
            )
        return result


_default_embedder: SentenceTransformerEmbedder | None = None


def get_embedder() -> Embedder:
    global _default_embedder
    if _default_embedder is None:
        _default_embedder = SentenceTransformerEmbedder()
    return _default_embedder
