### Dockefile for the Databases (Agensgraph + PgVector + Postgres)

Build the Docker image for DB. Tag and Push image to ghcr.io/cisco-eti
```
docker-compose up --build
```
Verify access to DB
```
docker exec -it ioc-knowledge-db psql -U postgresUser -d ioc-knowledge-db
```

