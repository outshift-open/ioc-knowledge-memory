FROM python:3.13.0-slim

# Add user app
RUN useradd -u 1001 app

# Create the app directory and set permissions to app
RUN mkdir /home/app/ && chown -R app:app /home/app

WORKDIR /home/app

# run the application as user app
USER app

COPY --chown=app:app pyproject.toml uv.lock ./

RUN pip3 install --user uv --break-system-packages
RUN /home/app/.local/bin/uv sync --no-dev --no-install-project

COPY --chown=app:app src/ ./src/

ENV PATH="/home/app/.venv/bin:$PATH"
ENV PYTHONPATH="/home/app/src"

# command to run on container start
CMD [ "uvicorn", "server.main:app", "--host", "0.0.0.0", "--port", "8000" ]
