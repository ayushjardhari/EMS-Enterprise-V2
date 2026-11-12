"""Turns a document's extracted text into embedded, section-tagged chunks."""
import logging
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.repositories.document_chunk_repository import DocumentChunkRepository
from app.services.embedding_service import Embedder, get_embedder
from app.services.section_chunking import chunk_document

logger = logging.getLogger(__name__)


class DocumentIndexingService:
    def __init__(self, db: Session, embedder: Embedder | None = None):
        self.db = db
        self.chunk_repo = DocumentChunkRepository(db)
        self._embedder = embedder

    @property
    def embedder(self) -> Embedder:
        return self._embedder or get_embedder()

    def index_document(self, document: Document) -> int:
        """(Re)build the chunks of one document. Returns the number of chunks stored.

        Embedding happens before any database change, so a failure leaves the
        previous chunks (if any) untouched.
        """
        if not document.extracted_text or not document.extracted_text.strip():
            self.chunk_repo.replace_for_document(document.id, [])
            document.indexing_status = "SKIPPED"
            document.indexed_at = None
            self.db.commit()
            return 0

        pieces = chunk_document(document.extracted_text)
        vectors = self.embedder.embed([p.content for p in pieces])
        chunks = [
            DocumentChunk(
                document_id=document.id,
                employee_id=document.employee_id,
                section=piece.section,
                chunk_index=piece.chunk_index,
                content=piece.content,
                embedding=vector,
                embedding_model=self.embedder.model_name,
            )
            for piece, vector in zip(pieces, vectors)
        ]
        self.chunk_repo.replace_for_document(document.id, chunks)
        document.indexing_status = "INDEXED"
        document.indexed_at = datetime.now(timezone.utc)
        self.db.commit()
        return len(chunks)

    def index_document_safely(self, document: Document) -> None:
        """Index without ever raising: a failed index must not fail an upload."""
        try:
            self.index_document(document)
        except Exception:
            logger.exception("Indexing failed for document %s", document.id)
            self.db.rollback()
            document.indexing_status = "FAILED"
            self.db.commit()
