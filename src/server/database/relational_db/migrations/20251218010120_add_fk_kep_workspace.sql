-- Add FK to knowledge_adapters without cascade: workspace_id -> workspaces.id
ALTER TABLE "knowledge_adapters"
  ADD CONSTRAINT "fk_kep_workspace"
  FOREIGN KEY ("workspace_id")
  REFERENCES "workspaces" ("id");
