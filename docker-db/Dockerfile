# Multi-stage build for multiarch (amd64 + arm64) support
FROM postgres:16-bookworm AS builder

ARG AGENSGRAPH_VERSION=v2.16.0

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libreadline-dev \
    zlib1g-dev \
    flex \
    bison \
    git \
    ca-certificates \
    libicu-dev \
    pkg-config \
    cmake \
    libssl-dev \
    libclang-dev \
    llvm-dev \
    postgresql-server-dev-16 \
    && rm -rf /var/lib/apt/lists/*

# Build AgensGraph
WORKDIR /tmp
RUN git clone --branch ${AGENSGRAPH_VERSION} https://github.com/skaiworldwide-oss/agensgraph.git \
    && cd agensgraph \
    && ./configure --prefix=/usr/local --with-openssl \
    && make -j$(nproc) \
    && make install

# Build pgvector
WORKDIR /tmp
RUN git clone --branch v0.8.1 https://github.com/pgvector/pgvector.git
WORKDIR /tmp/pgvector
RUN make USE_PGXS=1 OPTFLAGS=""
RUN make USE_PGXS=1 install

# Build TimescaleDB with Community license (enables compression + retention)
WORKDIR /tmp
RUN git clone --branch 2.17.2 https://github.com/timescale/timescaledb.git
WORKDIR /tmp/timescaledb
RUN ./bootstrap -DREGRESS_CHECKS=OFF -DTAP_CHECKS=OFF -DWARNINGS_AS_ERRORS=OFF -DUSE_OPENSSL=1
WORKDIR /tmp/timescaledb/build
RUN make
RUN make install

# Final stage - clean runtime image
FROM postgres:16-bookworm

# Copy AgensGraph binaries, libraries, and share files from builder.
# AgensGraph replaces core postgres binaries, so we must also copy the full
# share directory (includes postgres.bki required by initdb).
COPY --from=builder /usr/local/bin/ /usr/local/bin/
COPY --from=builder /usr/local/lib/ /usr/local/lib/
COPY --from=builder /usr/local/share/postgresql/ /usr/local/share/postgresql/

# Preload TimescaleDB shared library at startup
CMD ["postgres", "-c", "shared_preload_libraries=timescaledb"]

# Copy initialization script
COPY init-extensions.sql /docker-entrypoint-initdb.d/01-init-extensions.sql
