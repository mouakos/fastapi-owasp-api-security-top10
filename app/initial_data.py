"""Initial data setup for the application."""

from loguru import logger

from app.persistence.database import init_db


async def init() -> None:
    """Initialize the application with any necessary data."""
    # This function can be used to create initial data in the database, such as
    # default users, roles, or other entities required for the application to run.
    await init_db()


def main() -> None:
    """Main entry point for initializing the application."""
    logger.info("Initializing application data...")

    import asyncio

    asyncio.run(init())

    logger.info("Application data initialization complete.")


if __name__ == "__main__":
    main()
