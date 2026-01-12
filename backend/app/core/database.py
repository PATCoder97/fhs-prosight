"""
Database configuration and base models.

Provides SQLAlchemy declarative base and database session management.
"""

from sqlalchemy.orm import declarative_base

# SQLAlchemy declarative base for all models
Base = declarative_base()
