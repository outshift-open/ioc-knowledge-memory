#!/bin/bash
# Copyright 2026 Cisco Systems, Inc. and its affiliates
#
# SPDX-License-Identifier: Apache-2.0

set -e

# Start the application
echo "Starting application server..."
exec uvicorn server.main:app --host 0.0.0.0 --port 9003
