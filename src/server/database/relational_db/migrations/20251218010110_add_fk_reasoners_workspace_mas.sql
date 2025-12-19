-- Add FKs to reasoners without cascade: workspace_id -> workspaces.id, mas_id -> multi_agentic_systems.id
ALTER TABLE "reasoners"
  ADD CONSTRAINT "fk_reasoners_workspace"
  FOREIGN KEY ("workspace_id")
  REFERENCES "workspaces" ("id");

ALTER TABLE "reasoners"
  ADD CONSTRAINT "fk_reasoners_mas"
  FOREIGN KEY ("mas_id")
  REFERENCES "multi_agentic_systems" ("id");
