"""Pre-start script: run migrations and seed initial data."""

import asyncio
import subprocess
import sys

from loguru import logger


def run_migrations() -> None:
    """Run Alembic migrations."""
    logger.info("Running database migrations...")
    result = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        check=False,
    )
    if result.returncode != 0:
        logger.error("Migrations failed.")
        sys.exit(result.returncode)
    logger.info("Migrations complete.")


async def seed_data() -> None:
    """Seed initial data into the database."""
    from app.persistence.database import init_db

    logger.info("Seeding initial data...")
    await init_db()
    logger.info("Initial data seeding complete.")


def main() -> None:
    """Main entry point for pre-start tasks."""
    run_migrations()
    asyncio.run(seed_data())


if __name__ == "__main__":
    main()
