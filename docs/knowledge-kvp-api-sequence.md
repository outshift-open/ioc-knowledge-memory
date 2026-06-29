# Knowledge KeyValue Store API Sequence Diagrams

## MAS Scoped Key Value Store
```mermaid
sequenceDiagram
    participant IOCMP as ioc-mgmt-plane
    participant IOCCFN as ioc-cfn-svc
    participant IOCMS as ioc-knowledge-memory-svc
    participant DB as ioc-db

    %% 1. MAS Onboarding
    rect rgb(245, 255, 245)
        Note over IOCMP, IOCCFN: 1. MAS Onboarding
        IOCMP->>IOCCFN: POST /api/internal/workspaces/{workspaceId}/multi-agentic-systems/{masId}/shared-memories/keyvalue-store
    end

    %% 2. Store Onboarding
    rect rgb(245, 255, 245)
        Note over IOCCFN, IOCMS: 2. Store/MAS Onboarding
        IOCCFN->>IOCMS: POST /api/knowledge/kvps/stores/{store_id}
        Note right of IOCCFN: Create schema and tables
        IOCMS->>DB: CREATE SCHEMA, CREATE TABLE, CREATE INDEXES
        DB-->>IOCMS: Schema created
        IOCMS-->>IOCCFN: 201 Created
    end

    %% 3. Data Upsert
    rect rgb(255, 248, 240)
        Note over IOCCFN, IOCMS: 3. KVP Data Upsert
        IOCCFN->>IOCMS: POST /api/knowledge/kvps/
        Note right of IOCCFN: Upsert key-value pairs
        IOCMS->>DB: INSERT ... ON CONFLICT DO UPDATE
        DB-->>IOCMS: Records upserted
        IOCMS-->>IOCCFN: 201 Created
    end

    %% 4. Query Operations
    rect rgb(248, 240, 255)
        Note over IOCCFN, IOCMS: 4. KVP Query
        IOCCFN->>IOCMS: POST /api/knowledge/kvps/query
        Note right of IOCCFN: Query types: get_by_key
        IOCMS->>DB: SELECT with key lookup
        DB-->>IOCMS: Query results with timestamps
        IOCMS-->>IOCCFN: 200 OK
    end

    %% 5. Delete Operations
    rect rgb(255, 240, 240)
        Note over IOCCFN, IOCMS: 5. KVP Delete
        IOCCFN->>IOCMS: DELETE /api/knowledge/kvps
        Note right of IOCCFN: Delete by key
        IOCMS->>DB: DELETE with key lookup
        DB-->>IOCMS: Records deleted
        IOCMS-->>IOCCFN: 200 OK
    end
```

## Cognition Engine Scoped Key Value Store
```mermaid
sequenceDiagram
    participant IOCCE as cognition-engine
    participant IOCCFN as ioc-cfn-svc
    participant IOCMS as ioc-knowledge-memory-svc
    participant DB as ioc-db

    %% 1. CE Onboarding
    rect rgb(245, 255, 245)
        Note over IOCCE, IOCCFN: 1. CE Onboarding
        IOCCE->>IOCCFN: Existing CE onboarding Flow
    end

    %% 2. CE Store Onboarding
    rect rgb(245, 255, 245)
        Note over IOCCFN, IOCMS: 2. CE Store Onboarding using ce_id from registration
        IOCCFN->>IOCMS: POST /api/knowledge/kvps/stores/{store_id}
        Note right of IOCCFN: Create schema and tables
        IOCMS->>DB: CREATE SCHEMA, CREATE TABLE, CREATE INDEXES
        DB-->>IOCMS: Schema created
        IOCMS-->>IOCCFN: 201 Created
    end

    %% 3. Data Upsert
    rect rgb(255, 248, 240)
        Note over IOCCFN, IOCMS: 3. KVP Data Upsert
        IOCCFN->>IOCMS: POST /api/knowledge/kvps/
        Note right of IOCCFN: Upsert key-value pairs
        IOCMS->>DB: INSERT ... ON CONFLICT DO UPDATE
        DB-->>IOCMS: Records upserted
        IOCMS-->>IOCCFN: 201 Created
    end

    %% 4. Query Operations
    rect rgb(248, 240, 255)
        Note over IOCCFN, IOCMS: 4. KVP Query
        IOCCFN->>IOCMS: POST /api/knowledge/kvps/query
        Note right of IOCCFN: Query types: get_by_key
        IOCMS->>DB: SELECT with key lookup
        DB-->>IOCMS: Query results with timestamps
        IOCMS-->>IOCCFN: 200 OK
    end

    %% 5. Delete Operations
    rect rgb(255, 240, 240)
        Note over IOCCFN, IOCMS: 5. KVP Delete
        IOCCFN->>IOCMS: DELETE /api/knowledge/kvps
        Note right of IOCCFN: Delete by key
        IOCMS->>DB: DELETE with key lookup
        DB-->>IOCMS: Records deleted
        IOCMS-->>IOCCFN: 200 OK
    end
```


## API Endpoints

Refer to openapi-spec.yaml for all supported APIs and their details.