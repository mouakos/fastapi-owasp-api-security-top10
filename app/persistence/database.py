"""Database session management for asynchronous SQLModel operations."""

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlmodel import SQLModel, select
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel.pool import StaticPool

from app.core.config import settings


def _engine_kwargs() -> dict[str, object]:
    """Determine appropriate engine kwargs based on the database URL scheme."""
    if settings.database_url.startswith("sqlite+aiosqlite://"):
        return {
            "connect_args": {"check_same_thread": False},
            "poolclass": StaticPool,
        }
    return {
        "pool_pre_ping": True,  # enable connection health checks to automatically recycle stale connections, improving reliability in production environments
        "pool_size": 10,  # maintain a pool of 10 connections for efficient reuse under load, while allowing up to 20 additional connections during spikes with max_overflow
        "max_overflow": 20,  # allow up to 20 additional connections beyond the pool_size during high load
        "pool_timeout": 30,  # seconds to wait for a connection before raising an error
        "pool_recycle": 1800,  # recycle connections after 30 minutes to prevent stale connections in production environments
    }


async_engine = create_async_engine(
    url=settings.database_url,
    echo=settings.environment
    == "development",  # enable SQL query logging in development for debugging, disable in production for performance
    **_engine_kwargs(),
)

AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def create_tables() -> None:
    """Create database tables for all registered SQLModel models."""
    # Import models so SQLModel metadata includes all mapped tables.
    from app.persistence.models import Item, User  # noqa: F401

    async with async_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)


async def create_first_admin() -> None:
    """Create the first admin user from environment variables if not present.

    Reads FIRST_ADMIN_EMAIL, FIRST_ADMIN_USERNAME, and FIRST_ADMIN_PASSWORD
    from the environment (via Settings). Skips silently when any value is
    empty or an account with that email already exists.
    """
    from app.core.security.password import hash_password, validate_password_complexity
    from app.persistence.models.user import User, UserRole

    cfg = settings
    if not (cfg.first_admin_email and cfg.first_admin_username and cfg.first_admin_password):
        return

    async with AsyncSessionLocal() as session:
        existing = (
            await session.exec(select(User).where(User.email == cfg.first_admin_email))
        ).first()
        if existing:
            return

        password = cfg.first_admin_password.get_secret_value()
        if not validate_password_complexity(password):
            raise ValueError(
                "First admin password does not meet complexity requirements: "
                "must be 8-128 characters with uppercase, lowercase, digit, symbol, and no spaces."
                "Example of a valid password: 'AdminPass1!'"
            )
        admin = User(
            email=cfg.first_admin_email,
            username=cfg.first_admin_username,
            hashed_password=hash_password(password),
            role=UserRole.admin,
        )
        session.add(admin)
        await session.commit()


async def init_db() -> None:
    """Initialize the database by creating tables and seeding the first admin user."""
    # In production, you would typically run Alembic migrations instead of create_tables(),
    # but for development and testing, this can be a convenient way to ensure the schema is in place.
    # await create_tables()
    await create_first_admin()
