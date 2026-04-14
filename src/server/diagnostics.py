# Copyright 2026 Cisco Systems, Inc. and its affiliates
#
# SPDX-License-Identifier: Apache-2.0

"""Diagnostic API endpoints for TKF standard diagnostics."""

import datetime
import os

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


@diagnostics_router.get("/health")
async def health():
    """TKF standard health endpoint for liveness probe.

    Returns a simple status for k8s liveness probe and also includes
    detailed service state information.

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

    if service_state == HealthState.UP:
        return JSONResponse(content=response_body, status_code=200)
    elif service_state == HealthState.DEGRADED:
        return JSONResponse(content=response_body, status_code=503)
    else:
        return JSONResponse(content=response_body, status_code=500)


@diagnostics_router.get("/info")
async def info():
    """TKF standard info endpoint with git commit information.

    Returns:
        Dictionary with git commit information
    """
    return {
        "git": {
            "commit": {
                "time": os.environ.get("GIT_COMMIT_TIME", "unknown"),
                "id": os.environ.get("GIT_COMMIT_SHA", "unknown"),
            },
            "branch": os.environ.get("GIT_BRANCH", "main"),
        }
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
        JSON object with metric names from the Prometheus registry
    """
    metric_names = sorted({metric.name for metric in REGISTRY.collect() for _ in metric.samples})
    return {"metrics": metric_names}


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
