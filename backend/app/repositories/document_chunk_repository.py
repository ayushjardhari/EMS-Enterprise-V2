import uuid
from dataclasses import dataclass

from sqlalchemy import Float, select
from sqlalchemy.orm import Session

from app.models.document_chunk import DocumentChunk


@dataclass(frozen=True)
class ChunkHit:
    chunk: DocumentChunk
    distance: float  # cosine distance: 0 = identical direction, 2 = opposite

    @property
    def similarity(self) -> float:
        return 1.0 - self.distance


class DocumentChunkRepository:
    def __init__(self, db: Session):
        self.db = db

    def replace_for_document(self, document_id: uuid.UUID, chunks: list[DocumentChunk]) -> None:
        """Delete existing chunks of a document and insert the new ones (one commit)."""
        self.db.query(DocumentChunk).filter(DocumentChunk.document_id == document_id).delete(synchronize_session=False)
        self.db.add_all(chunks)
        self.db.commit()

    def count_for_document(self, document_id: uuid.UUID) -> int:
        return self.db.query(DocumentChunk).filter(DocumentChunk.document_id == document_id).count()

    def search_similar(
        self,
        query_embedding: list[float],
        limit: int = 20,
        employee_ids: list[uuid.UUID] | None = None,
        sections: list[str] | None = None,
    ) -> list[ChunkHit]:
        """Top-``limit`` chunks by cosine distance. PostgreSQL + pgvector only.

        ``employee_ids`` lets the caller apply structured filtering first
        (availability, role, department) and search only those candidates.
        """
        if self.db.get_bind().dialect.name != "postgresql":
            raise NotImplementedError("Vector similarity search requires PostgreSQL with pgvector")
        distance = DocumentChunk.embedding.op("<=>", return_type=Float)(query_embedding)
        stmt = select(DocumentChunk, distance.label("distance")).where(DocumentChunk.embedding.is_not(None))
        if employee_ids is not None:
            stmt = stmt.where(DocumentChunk.employee_id.in_(employee_ids))
        if sections:
            stmt = stmt.where(DocumentChunk.section.in_(sections))
        stmt = stmt.order_by(distance).limit(limit)
        return [ChunkHit(chunk=row[0], distance=float(row[1])) for row in self.db.execute(stmt).all()]
