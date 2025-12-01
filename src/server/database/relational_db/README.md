### Relational DB

TimescaleDB (Postgres17) is used as the Relational DB for this service.
https://www.tigerdata.com/docs/self-hosted/latest/install/installation-docker

#### Database Setup
```
docker compose -f docker/db.yaml up -d
``` 
If using non-default env variables, modify the docker file and setup env var as below in a .env file at the repo root.
```
'POSTGRES_DB', 'tkf_relational_db'
'POSTGRES_USER', 'postgresUser'
'POSTGRES_PASSWORD', 'postgresPW'
'POSTGRES_HOST', 'localhost'
'POSTGRES_PORT', '5455'
```
#### Schema Migration

Database migration is performed using Atlas.
https://atlasgo.io/guides/orms/sqlalchemy/getting-started

To perform migration related tasks, run the following command:
```
python scripts/atlas_migrate.py
```

1. To apply an existing atlas migration
Migrations as indicated by the existing migration scripts will be applied to the database.
```
python3 scripts/atlas_migrate.py apply 
```

2. To generate a new atlas migration 
If any new schema changes are added in relational_db/models, the below command will transform the models to .sql migration files in the migration folder.
```
python3 scripts/atlas_migrate.py generate "descriptive message for your migration"
```

#### Data Population
1. Populate the software table entries via script.
```
poetry run psql postgresql://postgresUser:postgresPW@localhost:5455/tkf_relational_db -f scripts/populate_software.sql
```