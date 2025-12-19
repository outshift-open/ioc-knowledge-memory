-- Add FK from multi_agentic_systems.workspace_id to workspaces.id without cascade
ALTER TABLE "multi_agentic_systems"
  ADD CONSTRAINT "fk_mas_workspace"
  FOREIGN KEY ("workspace_id")
  REFERENCES "workspaces" ("id");
