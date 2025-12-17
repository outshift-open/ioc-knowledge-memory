"""
Shared pytest fixtures and configuration for ci-tkf-data-logic-svc tests.
"""
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
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture(autouse=True)
def setup_test_environment():
    """Set up test environment with clean database."""

    try:
        db = RelationalDB()
        db.init()
        # Recreate database tables to always match current models
        Base.metadata.drop_all(bind=db.engine)
        Base.metadata.create_all(bind=db.engine)

        # Insert default software templates for testing
        session = db.session_factory()
        try:
            # Check if software templates already exist
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

    # Clean up after test
    try:
        db = RelationalDB()
        # Clean up database tables (keep schema)
        session = db.session_factory()
        try:
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
