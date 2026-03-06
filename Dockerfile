# Build stage
FROM python:3.11-slim AS builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Create build user and workspace
RUN useradd -u 1001 app && mkdir /home/app
WORKDIR /home/app

# Copy dependency files
COPY pyproject.toml poetry.lock ./

# Install poetry and dependencies
RUN pip3 install poetry \
    && poetry config virtualenvs.create false \
    && poetry install --only=main --no-root

# Runtime stage
FROM python:3.11-slim AS runtime

# Install only runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Create app user and directory
RUN useradd -u 1001 app \
    && mkdir /home/app \
    && chown -R app:app /home/app

WORKDIR /home/app

# Copy Python packages from builder stage
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application source and scripts
COPY --chown=app:app src/ ./src/
COPY --chown=app:app scripts/ ./scripts/
COPY --chown=app:app docker-entrypoint.sh ./

# Make entrypoint executable
RUN chmod +x docker-entrypoint.sh

# Switch to app user
USER app

# Set environment variables
ENV PYTHONPATH="/home/app/src"
ENV PATH="/home/app/bin:/home/app/.local/bin:$PATH"

# Use entrypoint script to run initializations if required, then start server
ENTRYPOINT ["/home/app/docker-entrypoint.sh"]
