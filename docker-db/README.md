### Dockerfile for the Database (AgensGraph + pgvector + TimescaleDB)

Built on [AgensGraph v2.16](https://github.com/bitnine-oss/agensgraph), a PostgreSQL 16 fork with native Cypher graph query support. The following extensions are compiled from source and included:

| Extension    | Version | Purpose                          |
|--------------|---------|----------------------------------|
| pgvector     | 0.8.1   | Vector similarity search         |
| TimescaleDB  | 2.17.2  | Time-series hypertables          |

**Changed in v2.2**: TimescaleDB now built with **Community license** (was Apache 2.0 in v2.1), enabling:
- ✅ **Compression** - 10-20x storage savings on time-series data
- ✅ **Retention policies** - Auto-delete old data
- ✅ **Continuous aggregates** - Pre-computed rollups

TimescaleDB `shared_preload_libraries` is baked into the image via `CMD`, so no extra flags are needed at runtime.

---

#### Build

```bash
docker compose up --build
```

Or build standalone:

```bash
docker build --platform linux/amd64 -t ioc-knowledge-db .
```

**Build time**: ~15-20 minutes (compiling TimescaleDB from source)

---

#### Tag & Push (manual)

1. Authenticate with GitHub Container Registry:

```bash
echo $GITHUB_TOKEN | docker login ghcr.io -u <github-username> --password-stdin
```

2. Tag the locally built image:

```bash
docker tag ioc-knowledge-db ghcr.io/cisco-eti/ioc-knowledge-memory-svc-db:2.2
```

3. Push to GHCR:

```bash
docker push ghcr.io/cisco-eti/ioc-knowledge-memory-svc-db:2.2
```

---

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

---

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

**Verify TimescaleDB license (IMPORTANT):**

```sql
SHOW timescaledb.license;
```

Expected: `timescale` (Community)  
✅ If `timescale` → Compression/retention available  
❌ If `apache` → Build failed, need to rebuild without cache

**Test compression:**

```sql
CREATE TABLE test_metrics (time TIMESTAMPTZ NOT NULL, value DOUBLE PRECISION);
SELECT create_hypertable('test_metrics', by_range('time', INTERVAL '1 day'));
ALTER TABLE test_metrics SET (timescaledb.compress, timescaledb.compress_orderby = 'time DESC');
SELECT compression_enabled FROM timescaledb_information.hypertables WHERE hypertable_name = 'test_metrics';
-- Should return: t (true)
```

---

#### What Changed from v2.1

| Feature | v2.1 | v2.2 |
|---------|------|------|
| TimescaleDB License | Apache 2.0 | Community (TSL) |
| Compression | ❌ | ✅ |
| Retention Policies | ❌ | ✅ |
| Continuous Aggregates | ❌ | ✅ |

**Single line change in Dockerfile:**
```diff
- RUN ./bootstrap -DREGRESS_CHECKS=OFF -DTAP_CHECKS=OFF -DWARNINGS_AS_ERRORS=OFF -DAPACHE_ONLY=1
+ RUN ./bootstrap -DREGRESS_CHECKS=OFF -DTAP_CHECKS=OFF -DWARNINGS_AS_ERRORS=OFF
```

Removing `-DAPACHE_ONLY=1` enables Community license.

---

#### Troubleshooting

**License shows `apache` instead of `timescale`:**

Cause: Docker cached old build layer.

Solution:
```bash
docker builder prune -a
docker build --no-cache --platform linux/amd64 -t ioc-knowledge-db .
```

**Compression commands fail:**

Check license first:
```sql
SHOW timescaledb.license;
```

If `apache`, rebuild image. If `timescale`, check error message.

---

#### Migration from v2.1

1. Pull new image and restart with same volume (data persists):
   ```bash
   docker pull ghcr.io/cisco-eti/ioc-knowledge-memory-svc-db:2.2
   docker-compose down
   docker-compose up -d
   ```

2. Verify license changed:
   ```bash
   docker exec <container-name> psql -U postgresUser -d ioc-knowledge-db -c "SHOW timescaledb.license;"
   # Should show: "timescale"
   ```

**No breaking changes** - fully backward compatible.

