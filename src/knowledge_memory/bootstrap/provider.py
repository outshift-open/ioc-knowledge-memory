# Copyright 2026 Cisco Systems, Inc. and its affiliates
#
# SPDX-License-Identifier: Apache-2.0

import logging
import os
import requests

logger = logging.getLogger(__name__)


def register_provider(
    provider_name: str,
    description: str,
    service_host: str,
    service_port: str,
    registration_url: str | None = None,
):
    """Register this service as a memory provider."""

    registration_url = registration_url or os.environ.get(
        "MEMORY_PROVIDER_REGISTRATION_URL"
    )
    if not registration_url:
        raise ValueError("MEMORY_PROVIDER_REGISTRATION_URL is required")

    service_url = f"http://{service_host}:{service_port}"

    payload = {
        "memory_provider_name": provider_name,
        "description": description,
        "config": {
            "url": service_url,
            "shared": "True",
        },
    }

    url = f"{registration_url.rstrip('/')}/api/memory-providers"

    response = requests.post(url, json=payload, timeout=30)

    if response.status_code in (201, 409):
        logger.info("Memory provider registration OK: %s", response.text)
        return

    raise RuntimeError(
        f"Unexpected response {response.status_code}: {response.text}"
    )
