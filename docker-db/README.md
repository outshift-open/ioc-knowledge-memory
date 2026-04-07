### Dockerfile for the Database (AgensGraph + pgvector + TimescaleDB)

Built on [AgensGraph v2.16](https://github.com/bitnine-oss/agensgraph), a PostgreSQL 16 fork with native Cypher graph query support. The following extensions are compiled from source and included:

| Extension    | Version | Purpose                          |
|--------------|---------|----------------------------------|
| pgvector     | 0.8.1   | Vector similarity search         |
| TimescaleDB  | 2.17.2  | Time-series hypertables          |

TimescaleDB `shared_preload_libraries` is baked into the image via `CMD`, so no extra flags are needed at runtime.

#### Build

```bash
docker compose up --build
```

Or build standalone:

```bash
docker build --platform linux/amd64 -t ioc-knowledge-db .
```

#### Tag & Push (manual)

1. Authenticate with GitHub Container Registry:

```bash
echo $GITHUB_TOKEN | docker login ghcr.io -u <github-username> --password-stdin
```

2. Tag the locally built image:

```bash
docker tag ioc-knowledge-db ghcr.io/cisco-eti/ioc-knowledge-memory-svc-db:2.0
```

3. Push to GHCR:

```bash
docker push ghcr.io/cisco-eti/ioc-knowledge-memory-svc-db:2.0
```

#### Run (standalone)

```bash
docker run -d \
  --name ioc-knowledge-db \
  -e POSTGRES_USER=postgresUser \
  -e POSTGRES_PASSWORD=postgresPass \
  -e POSTGRES_DB=ioc-knowledge-db \
  -p 5456:5432 \
  ioc-knowledge-db
```

#### Verify

Connect to the database:

```bash
docker exec -it ioc-knowledge-db psql -U postgresUser -d ioc-knowledge-db
```

Check extensions are loaded:

```sql
SELECT extname, extversion FROM pg_extension;
SHOW shared_preload_libraries;
```

