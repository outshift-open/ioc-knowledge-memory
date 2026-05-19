# Multi-stage build to reduce final image size
FROM skaiworldwide/agensgraph:v2.16.0-alpine3.22 AS builder

# Install build dependencies
RUN apk add --no-cache \
    git \
    build-base \
    clang \
    llvm-dev \
    make \
    postgresql-dev \
    cmake \
    openssl-dev

# Build pgvector
WORKDIR /tmp
RUN git clone --branch v0.8.1 https://github.com/pgvector/pgvector.git
WORKDIR /tmp/pgvector
RUN make USE_PGXS=1 OPTFLAGS=""
RUN make USE_PGXS=1 install

# Build TimescaleDB with Community license (enables compression + retention)
# Changed: Removed -DAPACHE_ONLY=1 flag to enable TimescaleDB Community features
WORKDIR /tmp
RUN git clone --branch 2.17.2 https://github.com/timescale/timescaledb.git
WORKDIR /tmp/timescaledb
RUN ./bootstrap -DREGRESS_CHECKS=OFF -DTAP_CHECKS=OFF -DWARNINGS_AS_ERRORS=OFF
WORKDIR /tmp/timescaledb/build
RUN make
RUN make install

# Final stage - clean runtime image
FROM skaiworldwide/agensgraph:v2.16.0-alpine3.22

# Copy only the compiled pgvector extension from builder
COPY --from=builder /usr/local/lib/postgresql/vector.so /usr/local/lib/postgresql/
COPY --from=builder /usr/local/share/postgresql/extension/vector* /usr/local/share/postgresql/extension/

# Copy compiled TimescaleDB extension from builder (now with Community features)
COPY --from=builder /usr/local/lib/postgresql/timescaledb*.so /usr/local/lib/postgresql/
COPY --from=builder /usr/local/share/postgresql/extension/timescaledb* /usr/local/share/postgresql/extension/

# Preload TimescaleDB shared library at startup
CMD ["postgres", "-c", "shared_preload_libraries=timescaledb"]

# Copy initialization script
COPY init-extensions.sql /docker-entrypoint-initdb.d/01-init-extensions.sql
