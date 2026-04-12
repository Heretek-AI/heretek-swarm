#!/usr/bin/env python3
"""
Migration Runner - Execute SQL migrations using Python

This script runs database migrations without requiring psql command.
Uses asyncpg for PostgreSQL connection.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


async def run_migration():
    """Run the swarm_memories table migration."""

    # Get database URL from environment
    database_url = os.getenv("DATABASE_URL", "")
    if not database_url:
        raise ValueError("DATABASE_URL environment variable is required")

    # Convert to asyncpg format
    if database_url.startswith("postgresql+asyncpg://"):
        database_url = database_url.replace("postgresql+asyncpg://", "postgresql://")


    try:
        import asyncpg

        # Connect to database
        conn = await asyncpg.connect(database_url)

        # Read migration file
        migration_path = Path(__file__).parent.parent / "migrations" / "001_create_swarm_memories.sql"
        with open(migration_path) as f:
            migration_sql = f.read()


        # Execute migration
        await conn.execute(migration_sql)


        # Verify table exists
        result = await conn.fetchval("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_name = 'swarm_memories'
            )
        """)

        if result:
            pass
        else:
            return False

        # Close connection
        await conn.close()

        return True

    except ImportError:
        return False
    except Exception:
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(run_migration())
    sys.exit(0 if success else 1)
