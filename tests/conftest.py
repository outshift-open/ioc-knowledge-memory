"""Pytest fixtures and minimal test DB bootstrap."""
import os
import time
import contextlib

import psycopg2

os.environ.setdefault("POSTGRES_DB", "tkf_test")
os.environ.setdefault("POSTGRES_USER", "postgresUser")
os.environ.setdefault("POSTGRES_PASSWORD", "postgresPW")
os.environ.setdefault("POSTGRES_HOST", "localhost")


def _ensure_test_database_exists(max_wait_seconds: int = 20) -> None:
    """Ensure the test database exists on the configured host.

    - Respects POSTGRES_HOST (e.g., 'tkf-relational-db' in CI)
    - Tries candidate ports: POSTGRES_PORT, 5432, 5455
    - Tries bootstrap DBs: 'postgres', 'tkf', 'template1'
    - Retries until max_wait_seconds for containers to become ready
    """
    db_name = os.environ.get("POSTGRES_DB", "tkf_test")
    user = os.environ.get("POSTGRES_USER", "postgresUser")
    password = os.environ.get("POSTGRES_PASSWORD", "postgresPW")
    host = os.environ.get("POSTGRES_HOST", "localhost")

    candidate_ports = []
    if os.environ.get("POSTGRES_PORT"):
        candidate_ports.append(str(os.environ["POSTGRES_PORT"]))
    for p in ("5432", "5455"):
        if p not in candidate_ports:
            candidate_ports.append(p)

    bootstrap_dbs = ("postgres", "tkf", "template1")

    deadline = time.time() + max_wait_seconds
    last_error = None

    while time.time() < deadline:
        for port in candidate_ports:
            for bootstrap_db in bootstrap_dbs:
                try:
                    conn = psycopg2.connect(
                        dbname=bootstrap_db,
                        user=user,
                        password=password,
                        host=host,
                        port=int(port),
                    )
                except Exception as e:
                    last_error = e
                    continue

                try:
                    conn.autocommit = True
                    with conn.cursor() as cur:
                        cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (db_name,))
                        exists = cur.fetchone() is not None
                        if not exists:
                            cur.execute(f'CREATE DATABASE "{db_name}"')
                    os.environ["POSTGRES_PORT"] = str(port)
                    return
                except Exception as e:
                    last_error = e
                finally:
                    with contextlib.suppress(Exception):
                        conn.close()
        time.sleep(1)

    if last_error:
        print(f"Test DB bootstrap warning: could not ensure '{db_name}' exists on {host}:{candidate_ports}. Last error: {last_error}")
    else:
        print(f"Test DB bootstrap warning: could not ensure '{db_name}' exists on {host}:{candidate_ports} (no connection attempts succeeded)")

import pytest
from fastapi.testclient import TestClient

from server.main import app
from server.database.relational_db.db import RelationalDB
from server.database.relational_db.models import Base
from server.database.relational_db.models.mas import MultiAgenticSystem
from server.database.relational_db.models.reasoner import Reasoner
from server.database.relational_db.models.knowledge_adapter import KnowledgeAdapter
from server.database.relational_db.models.software import Software
from server.database.relational_db.models.workspace import Workspace


@pytest.fixture
def client(setup_test_environment):
    """Create a test client for the FastAPI app after DB setup."""
    return TestClient(app)


@pytest.fixture(autouse=True)
def setup_test_environment():
    """Set up clean database per test session."""
    os.environ["POSTGRES_DB"] = "tkf_test"
    os.environ.setdefault("POSTGRES_USER", "postgresUser")
    os.environ.setdefault("POSTGRES_PASSWORD", "postgresPW")
    os.environ.setdefault("POSTGRES_HOST", "localhost")
    _ensure_test_database_exists()
    try:
        db = RelationalDB()
        db.init()
        Base.metadata.drop_all(bind=db.engine)
        Base.metadata.create_all(bind=db.engine)

        session = db.session_factory()
        try:
            existing_software = session.query(Software).filter(Software.type == "KnowledgeAdapterTemplates").first()
            if not existing_software:
                knowledge_adapter_templates = Software(
                    type="KnowledgeAdapterTemplates",
                    config={
                        "info-extraction": {
                            "use_crf": True,
                            "entities": ["PERSON", "ORG", "GPE", "DATE"],
                            "preprocessing": {"lowercase": False, "tokenizer": "wordpiece", "remove_punctuation": True},
                            "confidence_threshold": 0.85,
                        },
                        "otel": {
                            "resourceSpans": [
                                {
                                    "resource": {
                                        "attributes": [
                                            {"key": "service.name", "value": {"stringValue": "my-service"}},
                                            {"key": "host.name", "value": {"stringValue": "my-host"}},
                                        ]
                                    },
                                    "scopeSpans": [
                                        {
                                            "scope": {"name": "my-library", "version": "1.0.0"},
                                            "spans": [
                                                {
                                                    "kind": "SPAN_KIND_SERVER",
                                                    "name": "parent-operation",
                                                    "spanId": "abcdef0123456789",
                                                    "traceId": "0123456789abcdef0123456789abcdef",
                                                    "startTimeUnixNano": "1678886400000000000",
                                                    "endTimeUnixNano": "1678886400000000500",
                                                }
                                            ],
                                        }
                                    ],
                                }
                            ]
                        },
                    },
                )
                session.add(knowledge_adapter_templates)
                session.commit()
        except Exception as e:
            session.rollback()
            raise
        finally:
            session.close()
    except Exception as e:
        print(f"Database setup failed: {e}")
        pass

    yield

    try:
        db = RelationalDB()
        session = db.session_factory()
        try:
            session.query(Software).delete()
            session.query(KnowledgeAdapter).delete()
            session.query(Reasoner).delete()
            session.query(MultiAgenticSystem).delete()
            session.query(Workspace).delete()
            session.commit()
        except Exception:
            session.rollback()
        finally:
            session.close()
    except Exception:
        pass


@pytest.fixture
def sample_workspace_data():
    """Sample workspace data for testing."""
    return {"name": "Test Workspace"}


@pytest.fixture
def created_workspace(client, sample_workspace_data):
    """Create a workspace and return its ID."""
    response = client.post("/api/workspaces", json=sample_workspace_data)
    assert response.status_code == 201
    return response.json()["id"]
