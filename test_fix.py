import os
# Set DB_DSN to use SQLite in memory before importing any modules
os.environ["DB_DSN"] = "sqlite:///:memory:"

import logging
from bot.db.database import init_db
from bot.db.person_generator import clear_and_fill_persons_table

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
    """Test function to verify our fix."""
    logger.info("Starting test")

    # Initialize the database
    try:
        logger.info("Initializing database")
        init_db()
        logger.info("Database initialized successfully")

        # Clear and fill persons table
        clear_and_fill_persons_table()
        logger.info("Persons table cleared and filled with random data")

        logger.info("Test completed successfully!")
    except Exception as e:
        logger.error(f"Error: {e}")
        return

if __name__ == "__main__":
    main()
