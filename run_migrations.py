#!/usr/bin/env python3
"""
Script to run database migrations.
"""

import os
import logging
import argparse
import subprocess
from pathlib import Path

# Set up logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(),
    ],
)

logger = logging.getLogger(__name__)


def run_migrations(action="upgrade"):
    """
    Run database migrations using Alembic.

    Args:
        action: The Alembic action to perform (upgrade, downgrade, etc.)
    """
    logger.info(f"Running database migrations with action: {action}")

    # Get database connection string from environment variable
    DB_DSN = os.environ.get("DB_DSN")
    if not DB_DSN:
        logger.error("DB_DSN environment variable is not set")
        return False

    # Get the project root directory
    project_root = Path(__file__).parent

    # Run Alembic command
    try:
        if action == "upgrade":
            cmd = ["alembic", "upgrade", "head"]
        elif action == "downgrade":
            cmd = ["alembic", "downgrade", "-1"]
        elif action == "revision":
            cmd = [
                "alembic",
                "revision",
                "--autogenerate",
                "-m",
                "Auto-generated migration",
            ]
        else:
            logger.error(f"Unknown action: {action}")
            return False

        logger.info(f"Running command: {' '.join(cmd)}")
        result = subprocess.run(cmd, cwd=project_root, check=True)

        if result.returncode == 0:
            logger.info("Migrations completed successfully")
            return True
        else:
            logger.error(f"Migrations failed with return code: {result.returncode}")
            return False
    except subprocess.CalledProcessError as e:
        logger.error(f"Error running migrations: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error running migrations: {e}")
        return False


def main():
    """
    Main function to parse arguments and run migrations.
    """
    parser = argparse.ArgumentParser(description="Run database migrations")
    parser.add_argument(
        "action",
        choices=["upgrade", "downgrade", "revision"],
        default="upgrade",
        nargs="?",
        help="The migration action to perform",
    )

    args = parser.parse_args()

    success = run_migrations(args.action)

    if success:
        logger.info("Migration script completed successfully")
    else:
        logger.error("Migration script failed")
        exit(1)


if __name__ == "__main__":
    main()
