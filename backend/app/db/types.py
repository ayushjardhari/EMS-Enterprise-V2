"""
A UUID column type that works on both PostgreSQL (production/Docker) and
SQLite (the in-memory database used for fast unit tests).

Postgres has a native UUID type; SQLite doesn't, so this stores UUIDs as
plain 36-character strings there instead. Production behavior is
unaffected — this only changes what happens under the SQLite dialect.
"""
import uuid

from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.types import CHAR, TypeDecorator


class GUID(TypeDecorator):
    impl = CHAR
    cache_ok = True

    def __init__(self, as_uuid: bool = True, *args, **kwargs):
        # as_uuid is accepted for drop-in compatibility with
        # postgresql.UUID(as_uuid=True) call sites in the models — this
        # type always returns uuid.UUID objects regardless of the flag.
        super().__init__(*args, **kwargs)

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(PG_UUID(as_uuid=True))
        return dialect.type_descriptor(CHAR(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        if dialect.name == "postgresql":
            return str(value)
        return str(value) if not isinstance(value, uuid.UUID) else str(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        if isinstance(value, uuid.UUID):
            return value
        return uuid.UUID(value)
