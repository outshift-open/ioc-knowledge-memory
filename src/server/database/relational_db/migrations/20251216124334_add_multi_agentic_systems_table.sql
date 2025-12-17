-- Create "multi_agentic_systems" table
CREATE TABLE "multi_agentic_systems" (
  "id" character varying(36) NOT NULL DEFAULT (gen_random_uuid())::text,
  "workspace_id" character varying(36) NOT NULL,
  "name" character varying(255) NOT NULL,
  "description" text NULL,
  "agents" jsonb NULL,
  "config" jsonb NULL,
  "created_at" timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updated_at" timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  "created_by" character varying(255) NULL,
  "updated_by" character varying(255) NULL,
  "deleted_at" timestamp NULL,
  PRIMARY KEY ("id")
);

-- Create indexes
CREATE INDEX "idx_mas_workspace_id" ON "multi_agentic_systems" ("workspace_id");
CREATE INDEX "idx_mas_deleted_at" ON "multi_agentic_systems" ("deleted_at");
CREATE UNIQUE INDEX "idx_mas_workspace_name_unique" ON "multi_agentic_systems" ("workspace_id", "name") WHERE "deleted_at" IS NULL;
