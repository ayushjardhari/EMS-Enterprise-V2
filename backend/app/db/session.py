"""
SQLAlchemy engine and session factory.

One engine per process, one SessionLocal per request (see core/deps.py's
get_db). pool_pre_ping guards against stale connections after Postgres
restarts or idle timeouts, which matters once this runs for more than a
few hours continuously.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
