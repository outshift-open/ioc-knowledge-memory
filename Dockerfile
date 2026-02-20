FROM ghcr.io/cisco-eti/sre-python-docker:v3.11.9-hardened-debian-12

# Install curl for health checks, wget, postgresql-client
# AND build dependencies for agensgraph-python and other packages that may need compilation
RUN apt-get update && apt-get install -y curl wget postgresql-client build-essential libpq-dev && rm -rf /var/lib/apt/lists/*

# Add user app
RUN useradd -u 1001 app

# Create the app directory and set permissions to app
RUN mkdir /home/app/ && chown -R app:app /home/app

WORKDIR /home/app

COPY --chown=app:app pyproject.toml poetry.lock ./

# Install poetry and dependencies as root to avoid permission issues
RUN pip3 install poetry
RUN poetry config virtualenvs.create false
RUN poetry install --only=main --no-root

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
