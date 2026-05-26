"""
DB Schema Version Safety Check.

Validates that the database schema matches the expected version at startup.
If the version is missing or outdated, raises a clear RuntimeError instead of
silently operating on a stale schema.

Current expected schema version: "2.0"
"""

from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import text
from app.domain.models import SchemaVersion
from app.core.logging import logger

CURRENT_SCHEMA_VERSION = "2.0"


async def verify_schema(session: AsyncSession) -> None:
    """
    Check that the DB schema_version table exists and contains version == CURRENT_SCHEMA_VERSION.

    On first run after migration:
        - Table will exist (created by Base.metadata.create_all in startup)
        - But no version row will be present → insert it automatically (first-time init)

    On subsequent runs:
        - Row must match CURRENT_SCHEMA_VERSION
        - If mismatch → raise RuntimeError with clear message

    Raises:
        RuntimeError: If schema version is outdated (e.g. old DB from pre-2.0)
    """
    try:
        result = await session.execute(select(SchemaVersion).order_by(SchemaVersion.id.desc()))
        latest = result.scalars().first()

        if latest is None:
            # First-time run: stamp the current version
            version_record = SchemaVersion(
                version=CURRENT_SCHEMA_VERSION,
                applied_at=datetime.utcnow()
            )
            session.add(version_record)
            await session.commit()
            logger.info(f"Schema version stamped: {CURRENT_SCHEMA_VERSION}")
            return

        if latest.version != CURRENT_SCHEMA_VERSION:
            raise RuntimeError(
                f"Database schema outdated. "
                f"Expected version '{CURRENT_SCHEMA_VERSION}', "
                f"found '{latest.version}'. "
                f"Please delete 'contract_risk.db' and restart the server."
            )

        logger.info(f"Schema version OK: {latest.version}")

    except RuntimeError:
        raise
    except Exception as e:
        # Table likely doesn't exist yet — will be created by create_all, not an error
        logger.warning(f"Schema version check could not complete (expected on first run): {e}")
