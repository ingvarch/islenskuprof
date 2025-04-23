"""
Database connection module for the Telegram bot.
"""
import os
import logging
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

# Create SQLAlchemy engine
logger.info("Creating database engine")
engine = create_engine(DB_DSN)

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
    """
    session = Session()
    try:
        return session
    except Exception as e:
        session.rollback()
        logger.error(f"Error getting database session: {e}")
        raise

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
