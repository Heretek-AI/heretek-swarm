"""
Test fixtures for CLI tests.

Clears environment variables that are loaded by preload_modules in tests/config/test_seeding.py.
"""
import os
import tempfile
import warnings

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from heretek_swarm.config.db_models import Base


@pytest.fixture(autouse=True)
def clear_infrastructure_env_vars():
    """
    Clear infrastructure-related environment variables before each test.

    The preload_modules fixture in tests/config/test_seeding.py imports ConfigurationService
    which triggers load_dotenv() from the swarms package, setting DATABASE_URL and other
    infrastructure env vars from the .env file.

    This fixture ensures each test starts with a clean environment.
    """
    # Save original values
    saved = {}
    infra_vars = [
        "DATABASE_URL",
        "REDIS_URL",
        "QDRANT_HOST",
        "QDRANT_PORT",
        "QDRANT_URL",
        "HERETEK_NATS_URL",
        "NATS_SERVERS",
    ]
    for var in infra_vars:
        saved[var] = os.environ.get(var)
        os.environ.pop(var, None)

    yield

    # Restore original values
    for var, val in saved.items():
        if val is not None:
            os.environ[var] = val
        else:
            os.environ.pop(var, None)


@pytest.fixture(autouse=True)
def suppress_sqlalchemy_warnings():
    """Suppress SQLAlchemy warnings in CLI tests."""
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=Warning)
        yield


@pytest.fixture
def sync_test_db():
    """
    Create a file-based SQLite database for sync CLI tests.

    Uses a fresh temp file per test so the database is completely isolated.
    Returns a dict with:
    - 'url': the SQLite URL to set as DATABASE_URL
    - 'path': the temp file path for cleanup
    """
    db_path = tempfile.mktemp(suffix=".db")
    db_url = f"sqlite:///{db_path}"

    # Create engine and tables
    engine = create_engine(db_url, echo=False)
    Base.metadata.create_all(engine)

    yield {"url": db_url, "path": db_path, "engine": engine}

    # Cleanup
    engine.dispose()
    try:
        os.unlink(db_path)
    except OSError:
        pass
