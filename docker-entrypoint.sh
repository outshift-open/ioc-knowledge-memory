#!/bin/bash
set -e

# Start the application
echo "Starting application server..."
exec uvicorn server.main:app --host 0.0.0.0 --port 8001
