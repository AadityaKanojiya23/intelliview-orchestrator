"""
Shared pytest fixtures and configuration for the test suite.

These tests are designed to run against a live local stack (see docker-compose).
For unit tests that don't need Redis/Postgres, see test_unit_*.py.
"""

import os
import pathlib
import sys

import pytest
from testcontainers.postgres import PostgresContainer

# Make project root importable so `from config import ...` works.
ROOT = pathlib.Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Point at a local instance by default; tests can override via env.
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("POSTGRES_HOST", "localhost")
os.environ.setdefault("POSTGRES_DB", "ai_interview_db")
os.environ.setdefault("POSTGRES_USER", "postgres")
os.environ.setdefault("POSTGRES_PASSWORD", "postgres")
os.environ.setdefault("API_TOKEN", "test-token")

@pytest.fixture(scope="session")
def postgres_container():
    """Start a PostgreSQL Testcontainer for integration tests."""
    with PostgresContainer("postgres:16") as postgres:
        os.environ["POSTGRES_HOST"] = postgres.get_container_host_ip()
        os.environ["POSTGRES_PORT"] = str(postgres.get_exposed_port(5432))
        os.environ["POSTGRES_DB"] = postgres.dbname
        os.environ["POSTGRES_USER"] = postgres.username
        os.environ["POSTGRES_PASSWORD"] = postgres.password
        os.environ["DATABASE_URL"] = postgres.get_connection_url()
        yield postgres

@pytest.fixture(scope="session")
def api_base_url() -> str:
    return os.getenv("API_BASE_URL", "http://localhost:8000")
