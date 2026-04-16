# Copyright 2026 Cisco Systems, Inc. and its affiliates
#
# SPDX-License-Identifier: Apache-2.0

"""Diagnostic API endpoints for standard diagnostics."""

import datetime
import os
import platform
import socket
import sys
from urllib.parse import urlparse

from fastapi import APIRouter, Response, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field
from prometheus_client import REGISTRY

from app_logging import get_loggers_info, update_log_level
from server.common import service_name
from server.health_check import HealthState, check_self

diagnostics_router = APIRouter()


# Pydantic models for request/response validation
class LogLevelUpdate(BaseModel):
    """Model for updating log level."""

    model_config = ConfigDict(populate_by_name=True)

    module_name: str = Field(alias="module-name")
    log_level: str = Field(alias="log-level")


def _tcp_probe(host: str, port: int, timeout: float = 3.0) -> bool:
    """Return True if a TCP connection to host:port succeeds within timeout."""
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except Exception:
        return False


def _probe_url(url: str, timeout: float = 3.0) -> bool:
    """Parse url and TCP-probe its host+port."""
    try:
        if "://" not in url:
            url = "http://" + url
        parsed = urlparse(url)
        host = parsed.hostname or "localhost"
        port = parsed.port or (443 if parsed.scheme == "https" else 80)
        return _tcp_probe(host, port, timeout)
    except Exception:
        return False


@diagnostics_router.get("/health")
async def health(dependencies: bool = False):
    """Standard health endpoint for liveness probe.

    Returns a simple status for k8s liveness probe and also includes
    detailed service state information.

    When ?dependencies=true is passed, probes downstream services via TCP:
    - database (critical): PostgreSQL at IOC_KNOWLEDGE_DB_HOST:IOC_KNOWLEDGE_DB_PORT
    - management_plane (optional): ioc-mgmt-plane at MEMORY_PROVIDER_REGISTRATION_URL

    Returns:
        JSONResponse with health status and 200/500 status code
    """
    service_state = check_self()
    timestamp = datetime.datetime.now().isoformat()

    response_body = {
        "status": service_state.name,
        "service_name": service_name,
        "service_state": service_state.name,
        "last_updated": timestamp,
    }

    if dependencies:
        db_host = os.environ.get("IOC_KNOWLEDGE_DB_HOST", "localhost")
        db_port = int(os.environ.get("IOC_KNOWLEDGE_DB_PORT", "5456"))
        mgmt_url = os.environ.get("MEMORY_PROVIDER_REGISTRATION_URL", "http://localhost:8000")

        response_body["checks"] = {
            "database": _tcp_probe(db_host, db_port),
            "management_plane": _probe_url(mgmt_url),
        }

    if service_state in (HealthState.UP, HealthState.DEGRADED):
        return JSONResponse(content=response_body, status_code=200)
    else:
        return JSONResponse(content=response_body, status_code=500)


@diagnostics_router.get("/info")
async def info():
    """Standard info endpoint with service metadata and git commit information.

    Returns:
        Dictionary with service info and git commit information
    """
    try:
        from importlib.metadata import version as pkg_version
        ver = pkg_version("ioc-knowledge-memory-svc")
    except Exception:
        ver = os.environ.get("APPLICATION_VERSION", "unknown")

    return {
        "service": service_name,
        "version": ver,
        "python_version": sys.version,
        "platform": platform.platform(),
        "environment": os.environ.get("ENV", "development"),
        "git": {
            "commit": {
                "time": os.environ.get("GIT_COMMIT_TIME", "unknown"),
                "id": os.environ.get("GIT_COMMIT_SHA", "unknown"),
            },
            "branch": os.environ.get("GIT_BRANCH", "main"),
        },
    }


@diagnostics_router.get("/loggers")
async def get_loggers():
    """Get current log level configuration.

    Returns:
        Dictionary with logger information
    """
    return get_loggers_info()


@diagnostics_router.put(
    "/loggers",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def update_loggers(log_config: LogLevelUpdate):
    """Update log level for a specific module or root logger.

    Args:
        log_config: Log level update configuration

    Returns:
        204 on success, 400 with error message on failure
    """
    success, error_msg = update_log_level(log_config.module_name, log_config.log_level)

    if not success:
        return JSONResponse(content={"error": error_msg}, status_code=400)

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@diagnostics_router.get("/metrics")
async def metrics_list():
    """List available application metrics.

    Returns:
        JSON object with metric descriptors (name, type, help) from the Prometheus registry
    """
    metrics = []
    for metric in REGISTRY.collect():
        metrics.append({
            "name": metric.name,
            "type": metric.type,
            "help": metric.documentation,
        })
    return {"metrics": metrics}


@diagnostics_router.get("/metrics/{metric_name}")
async def get_metric(metric_name: str):
    """Get the value for a specific metric.

    Args:
        metric_name: Name of the metric to retrieve

    Returns:
        JSON object with metric samples, or 404 if not found
    """
    for metric_family in REGISTRY.collect():
        if metric_family.name == metric_name:
            samples = [
                {
                    "name": sample.name,
                    "labels": dict(sample.labels),
                    "value": sample.value,
                }
                for sample in metric_family.samples
            ]
            return {"metric_name": metric_name, "samples": samples}

    return JSONResponse(
        content={"error": f"Metric '{metric_name}' not found"},
        status_code=404,
    )
