#!/usr/bin/env python3
"""
Migration Runner Script
Runs SQL migrations against the PostgreSQL database.

Usage:
    python scripts/run_migrations.py              # Run all pending migrations
    python scripts/run_migrations.py --status     # Check migration status
    python scripts/run_migrations.py --rollback    # Rollback last migration (not implemented)
"""

import os
import sys
import argparse
import re
from pathlib import Path
from typing import Optional
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Database configuration from environment
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://heretek:heretek@localhost:5432/heretek")
MIGRATIONS_DIR = Path(__file__).parent.parent / "migrations"


def get_migration_files() -> list[Path]:
    """Get all SQL migration files sorted by version."""
    if not MIGRATIONS_DIR.exists():
        logger.error(f"Migrations directory not found: {MIGRATIONS_DIR}")
        return []
    
    migration_files = sorted(MIGRATIONS_DIR.glob("*.sql"))
    logger.info(f"Found {len(migration_files)} migration files")
    return migration_files


def parse_migration_header(content: str) -> dict:
    """Parse migration file header for metadata."""
    header = {}
    # Extract migration number and description from comments
    match = re.search(r"-- Migration: (\d+)", content)
    if match:
        header["version"] = match.group(1)
    
    match = re.search(r"-- Description: (.+)", content)
    if match:
        header["description"] = match.group(1)
    
    return header


def execute_migration(migration_file: Path) -> bool:
    """Execute a single migration file against the database."""
    import psycopg2
    from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
    
    content = migration_file.read_text()
    metadata = parse_migration_header(content)
    
    logger.info(f"Executing migration: {migration_file.name}")
    logger.info(f"  Description: {metadata.get('description', 'N/A')}")
    
    try:
        # Connect to database
        conn = psycopg2.connect(DATABASE_URL)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Split and execute statements (handling semicolons)
        # Remove comment lines for execution
        statements = []
        current_stmt = []
        
        for line in content.split("\n"):
            stripped = line.strip()
            # Skip pure comment lines but keep inline comments
            if stripped.startswith("--") and not stripped.startswith("-- Migration"):
                continue
            current_stmt.append(line)
            if stripped.endswith(";"):
                stmt = "\n".join(current_stmt)
                if stmt.strip():
                    statements.append(stmt)
                current_stmt = []
        
        # Execute each statement
        for i, stmt in enumerate(statements):
            stmt = stmt.strip()
            if not stmt:
                continue
            try:
                cursor.execute(stmt)
                logger.debug(f"  Executed statement {i+1}/{len(statements)}")
            except psycopg2.Error as e:
                logger.error(f"  Statement {i+1} failed: {e}")
                logger.error(f"  Statement: {stmt[:200]}...")
                conn.close()
                return False
        
        cursor.close()
        conn.close()
        
        logger.info(f"  Migration {migration_file.name} completed successfully")
        return True
        
    except ImportError:
        logger.error("psycopg2 not installed. Install with: pip install psycopg2-binary")
        return False
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        return False


def check_migration_status() -> None:
    """Check if migrations table exists and show status."""
    import psycopg2
    
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        # Check if migrations table exists
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'schema_migrations'
            );
        """)
        exists = cursor.fetchone()[0]
        
        if not exists:
            logger.info("No migrations table found. Run migrations to create it.")
        else:
            # Get applied migrations
            cursor.execute("SELECT version, applied_at FROM schema_migrations ORDER BY version")
            rows = cursor.fetchall()
            logger.info("Applied migrations:")
            for version, applied in rows:
                logger.info(f"  {version}: {applied}")
        
        # Check if swarm_memories table exists
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'swarm_memories'
            );
        """)
        exists = cursor.fetchone()[0]
        
        if exists:
            logger.info("\nswarm_memories table exists")
            # Show table structure
            cursor.execute("""
                SELECT column_name, data_type, is_nullable 
                FROM information_schema.columns 
                WHERE table_name = 'swarm_memories'
                ORDER BY ordinal_position
            """)
            columns = cursor.fetchall()
            logger.info("  Columns:")
            for col in columns:
                logger.info(f"    - {col[0]}: {col[1]} (nullable: {col[2]})")
            
            # Show indexes
            cursor.execute("""
                SELECT indexname, indexdef 
                FROM pg_indexes 
                WHERE tablename = 'swarm_memories'
            """)
            indexes = cursor.fetchall()
            logger.info("  Indexes:")
            for idx_name, idx_def in indexes:
                logger.info(f"    - {idx_name}")
        else:
            logger.info("\nswarm_memories table does not exist yet")
        
        cursor.close()
        conn.close()
        
    except ImportError:
        logger.error("psycopg2 not installed. Install with: pip install psycopg2-binary")
    except Exception as e:
        logger.error(f"Failed to check status: {e}")


def create_migrations_table() -> bool:
    """Create the migrations tracking table."""
    import psycopg2
    from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
    
    try:
        conn = psycopg2.connect(DATABASE_URL)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version VARCHAR(50) PRIMARY KEY,
                description TEXT,
                applied_at TIMESTAMP DEFAULT NOW()
            );
        """)
        
        cursor.close()
        conn.close()
        logger.info("Created schema_migrations table")
        return True
        
    except Exception as e:
        logger.error(f"Failed to create migrations table: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Run database migrations")
    parser.add_argument(
        "--status", 
        action="store_true", 
        help="Check migration status"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be executed without running"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force run all migrations (skip tracking)"
    )
    
    args = parser.parse_args()
    
    if args.status:
        check_migration_status()
        return 0
    
    # Create migrations tracking table if needed
    if not args.dry_run:
        create_migrations_table()
    
    # Get and execute migrations
    migration_files = get_migration_files()
    
    if args.dry_run:
        logger.info("Dry run - would execute:")
        for mf in migration_files:
            logger.info(f"  - {mf.name}")
        return 0
    
    success_count = 0
    failed_count = 0
    
    for mf in migration_files:
        if execute_migration(mf):
            success_count += 1
        else:
            failed_count += 1
            logger.error(f"Migration {mf.name} failed")
    
    logger.info(f"\nMigration Summary:")
    logger.info(f"  Succeeded: {success_count}")
    logger.info(f"  Failed: {failed_count}")
    
    return 1 if failed_count > 0 else 0


if __name__ == "__main__":
    sys.exit(main())