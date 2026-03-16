"""Database session management for asynchronous SQLModel operations."""

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlmodel import SQLModel, select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.config import settings

async_engine = create_async_engine(
    url=settings.database_url,
    echo=False,
)

AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def seed_admin() -> None:
    """Create the first admin user from environment variables if not present.

    Reads FIRST_ADMIN_EMAIL, FIRST_ADMIN_USERNAME, and FIRST_ADMIN_PASSWORD
    from the environment (via Settings). Skips silently when any value is
    empty or an account with that email already exists.
    """
    from app.persistence.models.user import User, UserRole
    from app.security.password import hash_password

    cfg = settings
    if not (cfg.first_admin_email and cfg.first_admin_username and cfg.first_admin_password):
        return

    async with AsyncSessionLocal() as session:
        existing = (
            await session.exec(select(User).where(User.email == cfg.first_admin_email))
        ).first()
        if existing:
            return

        admin = User(
            email=cfg.first_admin_email,
            username=cfg.first_admin_username,
            hashed_password=hash_password(cfg.first_admin_password.get_secret_value()),
            role=UserRole.admin,
        )
        session.add(admin)
        await session.commit()


async def init_db() -> None:
    """Initialize database schema for all registered SQLModel tables."""
    # Import models so SQLModel metadata includes all mapped tables.
    from app.persistence.models import item, user  # noqa: F401

    async with async_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    await seed_admin()
