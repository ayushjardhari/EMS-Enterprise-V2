"""
Declarative base for all ORM models.

Deliberately contains ONLY the Base class — no model imports here. Models
import Base from this module, so if this module also imported the models
back, Python would hit a circular-import error the moment any single
model file loads. Model registration into Base.metadata (needed for
Alembic autogeneration) happens instead via app/models/__init__.py.
"""
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass
