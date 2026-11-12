"""pgvector extension, document_chunks table with HNSW index, document indexing status

Revision ID: 0004
Revises: 0003

The vector dimension (384) matches sentence-transformers/all-MiniLM-L6-v2.
Using a model with a different dimension requires a new migration.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg
from pgvector.sqlalchemy import Vector

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None

EMBEDDING_DIM = 384


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.add_column("documents", sa.Column("indexing_status", sa.String(30), nullable=False, server_default="NOT_INDEXED"))
    op.add_column("documents", sa.Column("indexed_at", sa.DateTime(timezone=True), nullable=True))

    uuid = pg.UUID(as_uuid=True)
    op.create_table(
        "document_chunks",
        sa.Column("id", uuid, primary_key=True),
        sa.Column("document_id", uuid, sa.ForeignKey("documents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("employee_id", uuid, sa.ForeignKey("employees.id", ondelete="CASCADE"), nullable=False),
        sa.Column("section", sa.String(50), nullable=False),
        sa.Column("page_number", sa.Integer(), nullable=True),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("embedding", Vector(EMBEDDING_DIM), nullable=True),
        sa.Column("embedding_model", sa.String(150), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("document_id", "chunk_index", name="uq_document_chunk_index"),
    )
    op.create_index("ix_document_chunks_document_id", "document_chunks", ["document_id"])
    op.create_index("ix_document_chunks_employee_id", "document_chunks", ["employee_id"])
    op.create_index("ix_document_chunks_section", "document_chunks", ["section"])
    # Approximate nearest-neighbour index for cosine distance (the <=> operator).
    op.execute(
        "CREATE INDEX ix_document_chunks_embedding_hnsw ON document_chunks "
        "USING hnsw (embedding vector_cosine_ops) WITH (m = 16, ef_construction = 64)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_document_chunks_embedding_hnsw")
    op.drop_table("document_chunks")
    op.drop_column("documents", "indexed_at")
    op.drop_column("documents", "indexing_status")
    # The vector extension is left installed on purpose.
