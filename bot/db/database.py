"""
Database connection module for the Telegram bot.
"""
import os
import logging
from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session

# Get logger for this module
logger = logging.getLogger(__name__)

# Get database connection string from environment variable
DB_DSN = os.environ.get("DB_DSN")
if not DB_DSN:
    logger.error("DB_DSN environment variable is not set")
    raise ValueError("DB_DSN environment variable is not set")

# Create SQLAlchemy engine with connection pool settings
logger.info("Creating database engine")
engine = create_engine(
    DB_DSN,
    pool_size=5,           # Number of connections to keep in pool
    max_overflow=10,       # Additional connections allowed when pool is exhausted
    pool_recycle=3600,     # Recycle connections after 1 hour (prevents stale connections)
    pool_pre_ping=True     # Test connection health before using
)

# Create session factory
SessionFactory = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create scoped session
Session = scoped_session(SessionFactory)

# Create base class for models
Base = declarative_base()

def get_db_session():
    """
    Get a database session.

    Returns:
        SQLAlchemy session

    Note:
        Caller is responsible for closing the session.
        Prefer using db_session() context manager instead.
    """
    return Session()


@contextmanager
def db_session(auto_commit: bool = True):
    """
    Context manager for database sessions with automatic cleanup.

    Args:
        auto_commit: If True, commits on successful exit. Default True.

    Yields:
        SQLAlchemy session

    Example:
        with db_session() as session:
            user = session.query(User).filter_by(id=1).first()
            user.name = "New Name"
        # Auto-commits and cleans up
    """
    session = Session()
    try:
        yield session
        if auto_commit:
            session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        Session.remove()  # Proper cleanup for scoped_session

def init_db():
    """
    Initialize the database.
    """
    logger.info("Initializing database")
    try:
        # Import models to ensure they are registered with the Base
        from bot.db import models
        
        # Create tables if they don't exist
        Base.metadata.create_all(bind=engine)
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise
