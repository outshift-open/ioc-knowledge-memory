### Relational DB

#### Database Setup
```
docker compose -f docker/neo4j_no_auth.yaml up -d
``` 
Optionally - Set the below env variables in a .env file at the repo root (If using non-default values).
```
NEO4J_DATABASE=tkf
NEO4J_HOST=localhost
NEO4J_PORT=7687 # Used by server
NEO4J_PORT_HTTP=7474 # Used for UI
```

