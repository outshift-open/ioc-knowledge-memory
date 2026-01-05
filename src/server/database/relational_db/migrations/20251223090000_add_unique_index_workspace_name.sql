-- Enforce unique active workspace names (allow reuse after soft delete)
CREATE UNIQUE INDEX IF NOT EXISTS idx_workspace_name_unique
ON "workspace" ("name")
WHERE "deleted_at" IS NULL;
