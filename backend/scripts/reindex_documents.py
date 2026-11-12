"""Index existing documents and sanity-check vector search.

Run inside the backend container:

    docker compose exec backend python -m scripts.reindex_documents
    docker compose exec backend python -m scripts.reindex_documents --query "kubernetes deployment experience"
"""
import argparse

from app.db.session import SessionLocal
import app.models  # noqa: F401
from app.models.document import Document
from app.repositories.document_chunk_repository import DocumentChunkRepository
from app.services.document_indexing_service import DocumentIndexingService
from app.services.embedding_service import get_embedder


def reindex(only_pending: bool) -> None:
    with SessionLocal() as db:
        query = db.query(Document).filter(Document.extraction_status == "COMPLETED")
        if only_pending:
            query = query.filter(Document.indexing_status != "INDEXED")
        documents = query.all()
        service = DocumentIndexingService(db)
        print(f"Indexing {len(documents)} document(s)...")
        for document in documents:
            count = service.index_document(document)
            print(f"  {document.filename}: {count} chunk(s)")


def search(text: str, limit: int) -> None:
    embedder = get_embedder()
    vector = embedder.embed([text])[0]
    with SessionLocal() as db:
        hits = DocumentChunkRepository(db).search_similar(vector, limit=limit)
        for rank, hit in enumerate(hits, 1):
            preview = hit.chunk.content.replace("\n", " ")[:110]
            print(f"{rank:>2}. sim={hit.similarity:.3f} [{hit.chunk.section}] emp={hit.chunk.employee_id} | {preview}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--all", action="store_true", help="re-index every document, not just pending ones")
    parser.add_argument("--query", help="run a test similarity search after indexing")
    parser.add_argument("--limit", type=int, default=5)
    args = parser.parse_args()
    reindex(only_pending=not args.all)
    if args.query:
        search(args.query, args.limit)
