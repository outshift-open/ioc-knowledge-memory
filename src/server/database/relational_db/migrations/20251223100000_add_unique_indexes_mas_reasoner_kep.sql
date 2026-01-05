-- Clean duplicates and enforce unique active names per workspace

-- Multi-Agentic System duplicates cleanup
WITH dups AS (
  SELECT id,
         ROW_NUMBER() OVER (
           PARTITION BY workspace_id, name
           ORDER BY created_at DESC, id DESC
         ) AS rn
  FROM "multi_agentic_system"
  WHERE "deleted_at" IS NULL
)
UPDATE "multi_agentic_system" t
SET "deleted_at" = CURRENT_TIMESTAMP
FROM dups
WHERE dups.id = t.id AND dups.rn > 1;

-- Reasoner duplicates cleanup
WITH dups AS (
  SELECT id,
         ROW_NUMBER() OVER (
           PARTITION BY workspace_id, name
           ORDER BY created_at DESC, id DESC
         ) AS rn
  FROM "reasoner"
  WHERE "deleted_at" IS NULL
)
UPDATE "reasoner" t
SET "deleted_at" = CURRENT_TIMESTAMP
FROM dups
WHERE dups.id = t.id AND dups.rn > 1;

-- Knowledge Adapter duplicates cleanup
WITH dups AS (
  SELECT id,
         ROW_NUMBER() OVER (
           PARTITION BY workspace_id, name
           ORDER BY created_at DESC, id DESC
         ) AS rn
  FROM "knowledge_adapter"
  WHERE "deleted_at" IS NULL
)
UPDATE "knowledge_adapter" t
SET "deleted_at" = CURRENT_TIMESTAMP
FROM dups
WHERE dups.id = t.id AND dups.rn > 1;

-- Create partial unique indexes (allow reuse after soft delete)
CREATE UNIQUE INDEX IF NOT EXISTS idx_mas_workspace_name_unique
ON "multi_agentic_system" ("workspace_id", "name")
WHERE "deleted_at" IS NULL;

CREATE UNIQUE INDEX IF NOT EXISTS idx_reasoner_workspace_name_unique
ON "reasoner" ("workspace_id", "name")
WHERE "deleted_at" IS NULL;

CREATE UNIQUE INDEX IF NOT EXISTS idx_kep_workspace_name_unique
ON "knowledge_adapter" ("workspace_id", "name")
WHERE "deleted_at" IS NULL;
