"""Tests for Diagnostics API endpoints."""

from types import SimpleNamespace
from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from server.diagnostics import diagnostics_router
from server.health_check import HealthState

# Create a test FastAPI app
app = FastAPI()
app.include_router(diagnostics_router, prefix="/api/internal/diagnostics")

# Test client
client = TestClient(app)

PREFIX = "/api/internal/diagnostics"


class TestHealthEndpoint:
    """Tests for GET /health."""

    @patch("server.diagnostics.check_self", return_value=HealthState.UP)
    def test_health_up(self, mock_check):
        response = client.get(f"{PREFIX}/health")
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "UP"
        assert body["service_state"] == "UP"
        assert "service_name" in body
        assert "last_updated" in body

    @patch("server.diagnostics.check_self", return_value=HealthState.DEGRADED)
    def test_health_degraded_returns_503(self, mock_check):
        response = client.get(f"{PREFIX}/health")
        assert response.status_code == 503
        body = response.json()
        assert body["status"] == "DEGRADED"
        assert body["service_state"] == "DEGRADED"

    @patch("server.diagnostics.check_self", return_value=HealthState.DOWN)
    def test_health_down_returns_500(self, mock_check):
        response = client.get(f"{PREFIX}/health")
        assert response.status_code == 500
        body = response.json()
        assert body["status"] == "DOWN"
        assert body["service_state"] == "DOWN"

    @patch("server.diagnostics.check_self", return_value=HealthState.UNKNOWN)
    def test_health_unknown_returns_500(self, mock_check):
        response = client.get(f"{PREFIX}/health")
        assert response.status_code == 500
        body = response.json()
        assert body["status"] == "UNKNOWN"
        assert body["service_state"] == "UNKNOWN"


class TestInfoEndpoint:
    """Tests for GET /info."""

    @patch.dict(
        "os.environ",
        {
            "GIT_COMMIT_TIME": "2026-01-01T00:00:00",
            "GIT_COMMIT_SHA": "abc123",
            "GIT_BRANCH": "feature/test",
        },
    )
    def test_info_with_env_vars(self):
        response = client.get(f"{PREFIX}/info")
        assert response.status_code == 200
        body = response.json()
        assert body["git"]["commit"]["time"] == "2026-01-01T00:00:00"
        assert body["git"]["commit"]["id"] == "abc123"
        assert body["git"]["branch"] == "feature/test"

    @patch.dict("os.environ", {}, clear=True)
    def test_info_defaults_when_env_missing(self):
        response = client.get(f"{PREFIX}/info")
        assert response.status_code == 200
        body = response.json()
        assert body["git"]["commit"]["time"] == "unknown"
        assert body["git"]["commit"]["id"] == "unknown"
        assert body["git"]["branch"] == "main"


class TestLoggersEndpoint:
    """Tests for GET and POST /loggers."""

    @patch(
        "server.diagnostics.get_loggers_info",
        return_value={"log-level": "INFO", "loggers": {"server": "DEBUG"}},
    )
    def test_get_loggers(self, mock_get):
        response = client.get(f"{PREFIX}/loggers")
        assert response.status_code == 200
        body = response.json()
        assert body["log-level"] == "INFO"
        assert body["loggers"]["server"] == "DEBUG"
        mock_get.assert_called_once()

    @patch("server.diagnostics.update_log_level", return_value=(True, None))
    def test_put_loggers_success(self, mock_update):
        response = client.put(
            f"{PREFIX}/loggers",
            json={"module-name": "ROOT", "log-level": "DEBUG"},
        )
        assert response.status_code == 204
        mock_update.assert_called_once_with("ROOT", "DEBUG")

    @patch("server.diagnostics.update_log_level", return_value=(False, "Invalid log level"))
    def test_put_loggers_error(self, mock_update):
        response = client.put(
            f"{PREFIX}/loggers",
            json={"module-name": "ROOT", "log-level": "INVALID"},
        )
        assert response.status_code == 400
        assert response.json()["error"] == "Invalid log level"

    def test_put_loggers_missing_fields(self):
        response = client.put(f"{PREFIX}/loggers", json={})
        assert response.status_code == 422


class TestMetricsEndpoints:
    """Tests for GET /metrics and GET /metrics/{metric_name}."""

    @patch("server.diagnostics.REGISTRY")
    def test_metrics_list(self, mock_registry):
        mock_registry.collect.return_value = [
            SimpleNamespace(
                name="http_requests",
                samples=[SimpleNamespace(name="http_requests_total", labels={}, value=10.0)],
            ),
            SimpleNamespace(
                name="process_cpu",
                samples=[SimpleNamespace(name="process_cpu_seconds_total", labels={}, value=1.5)],
            ),
        ]
        response = client.get(f"{PREFIX}/metrics")
        assert response.status_code == 200
        body = response.json()
        assert "metrics" in body
        assert body["metrics"] == ["http_requests", "process_cpu"]

    @patch("server.diagnostics.REGISTRY")
    def test_get_metric_success(self, mock_registry):
        mock_registry.collect.return_value = [
            SimpleNamespace(
                name="http_requests",
                samples=[
                    SimpleNamespace(
                        name="http_requests_total",
                        labels={"method": "GET", "path": "/health"},
                        value=42.0,
                    ),
                ],
            ),
        ]
        response = client.get(f"{PREFIX}/metrics/http_requests")
        assert response.status_code == 200
        body = response.json()
        assert body["metric_name"] == "http_requests"
        assert len(body["samples"]) == 1
        assert body["samples"][0]["name"] == "http_requests_total"
        assert body["samples"][0]["labels"] == {"method": "GET", "path": "/health"}
        assert body["samples"][0]["value"] == 42.0

    @patch("server.diagnostics.REGISTRY")
    def test_get_metric_not_found(self, mock_registry):
        mock_registry.collect.return_value = []
        response = client.get(f"{PREFIX}/metrics/nonexistent_metric")
        assert response.status_code == 404
        assert "not found" in response.json()["error"]
