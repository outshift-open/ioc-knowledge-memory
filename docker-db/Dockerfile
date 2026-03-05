# Multi-stage build to reduce final image size
FROM skaiworldwide/agensgraph:v2.16.0-alpine3.22 AS builder

# Install build dependencies
RUN apk add --no-cache \
    git \
    build-base \
    clang \
    llvm-dev \
    make \
    postgresql-dev

# Build pgvector
WORKDIR /tmp
RUN git clone --branch v0.8.1 https://github.com/pgvector/pgvector.git
WORKDIR /tmp/pgvector
RUN make USE_PGXS=1
RUN make USE_PGXS=1 install

# Final stage - clean runtime image
FROM skaiworldwide/agensgraph:v2.16.0-alpine3.22

# Copy only the compiled pgvector extension from builder
COPY --from=builder /usr/local/lib/postgresql/vector.so /usr/local/lib/postgresql/
COPY --from=builder /usr/local/share/postgresql/extension/vector* /usr/local/share/postgresql/extension/

# Copy initialization script
COPY init-extensions.sql /docker-entrypoint-initdb.d/01-init-extensions.sql
