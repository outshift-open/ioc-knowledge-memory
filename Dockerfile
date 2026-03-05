FROM ghcr.io/cisco-eti/sre-python-docker:v3.11.9-hardened-debian-12

# Install only essential runtime dependencies and build dependencies in one layer
RUN apt-get update && apt-get install -y \
    # Runtime dependencies
    curl \
    postgresql-client \
    # Build dependencies (will be removed later)
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Add user app and create directory in one layer
RUN useradd -u 1001 app \
    && mkdir /home/app/ \
    && chown -R app:app /home/app

WORKDIR /home/app

COPY --chown=app:app pyproject.toml poetry.lock ./

# Install poetry and dependencies, then remove build dependencies in same layer
RUN pip3 install poetry \
    && poetry config virtualenvs.create false \
    && poetry install --only=main --no-root \
    && apt-get purge -y build-essential \
    && apt-get autoremove -y \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && pip3 uninstall -y poetry

# Copy application source and scripts
COPY --chown=app:app src/ ./src/
COPY --chown=app:app scripts/ ./scripts/
COPY --chown=app:app docker-entrypoint.sh ./

# Make entrypoint executable
RUN chmod +x docker-entrypoint.sh

# run the application as user app
USER app

ENV PYTHONPATH="/home/app/src"
ENV PATH="/home/app/bin:/home/app/.local/bin:$PATH"

# Use entrypoint script to run initializations if required, then start server
ENTRYPOINT ["/home/app/docker-entrypoint.sh"]
