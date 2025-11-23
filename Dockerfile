FROM ghcr.io/cisco-eti/sre-python-docker:v3.11.9-hardened-debian-12

# Add user app
RUN useradd -u 1001 app

# Create the app directory and set permissions to app
RUN mkdir /home/app/ && chown -R app:app /home/app

WORKDIR /home/app

# run the application as user app
USER app

COPY --chown=app:app pyproject.toml poetry.lock ./

RUN pip3 install --user poetry --break-system-packages
RUN /home/app/.local/bin/poetry config virtualenvs.create false
RUN /home/app/.local/bin/poetry install --only=main --no-root

COPY --chown=app:app src/ ./src/

ENV PYTHONPATH="/home/app/src"
ENV PATH="/home/app/.local/bin:$PATH"

# command to run on container start
CMD [ "uvicorn", "server.main:app", "--host", "0.0.0.0", "--port", "8000" ]
