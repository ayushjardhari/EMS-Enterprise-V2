"""
Embedding column type that works on PostgreSQL (pgvector) and SQLite.

Production/Docker uses a real pgvector ``vector(N)`` column. The unit tests
run on in-memory SQLite (see tests/conftest.py), which has no vector type,
so there the same column falls back to JSON. Similarity search itself is
PostgreSQL-only; SQLite is just enough to store and read vectors in tests.
"""
from pgvector.sqlalchemy import Vector
from sqlalchemy.types import JSON, TypeDecorator


class EmbeddingVector(TypeDecorator):
    impl = JSON
    cache_ok = True

    def __init__(self, dim: int, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.dim = dim

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(Vector(self.dim))
        return dialect.type_descriptor(JSON())

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        return [float(x) for x in value]

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        # pgvector returns a numpy array / list; JSON returns a list.
        return [float(x) for x in value]
