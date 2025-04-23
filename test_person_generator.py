#!/usr/bin/env python3
"""
Test script for the person generator.
"""
import logging
import os
import sys

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(),
    ]
)

logger = logging.getLogger(__name__)

def main():
    """Test the person generator."""
    logger.info("Testing person generator")

    # Check if DB_DSN is set
    if not os.environ.get("DB_DSN"):
        logger.error("DB_DSN environment variable is not set")
        sys.exit(1)

    # Initialize the database
    try:
        from bot.db.database import init_db
        logger.info("Initializing database")
        init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        sys.exit(1)

    # Clear and fill persons table
    try:
        from bot.db.person_generator import clear_and_fill_persons_table
        logger.info("Clearing and filling persons table")
        clear_and_fill_persons_table()
        logger.info("Persons table cleared and filled with random data")
    except Exception as e:
        logger.error(f"Error clearing and filling persons table: {e}")
        sys.exit(1)

    # Check that 30 persons were created
    try:
        from bot.db.database import get_db_session
        from bot.db.models import Person
        session = get_db_session()
        count = session.query(Person).count()
        logger.info(f"Found {count} persons in the database")
        if count == 30:
            logger.info("Test passed: 30 persons were created")
        else:
            logger.error(f"Test failed: Expected 30 persons, found {count}")
            sys.exit(1)
    except Exception as e:
        logger.error(f"Error checking persons count: {e}")
        sys.exit(1)
    finally:
        session.close()

    logger.info("All tests passed")

if __name__ == "__main__":
    main()
