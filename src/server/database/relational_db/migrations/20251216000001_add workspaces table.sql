-- Create "workspaces" table
CREATE TABLE "workspaces" (
  "id" character varying(36) NOT NULL DEFAULT (gen_random_uuid())::text,
  "name" character varying(255) NOT NULL,
  "users" character varying[] NULL,
  "config" jsonb NULL,
  "created_at" timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updated_at" timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  "created_by" character varying(255) NULL,
  "updated_by" character varying(255) NULL,
  "deleted_at" timestamp NULL,
  PRIMARY KEY ("id")
);
-- Create index "idx_workspace_name" to table: "workspaces"
CREATE INDEX "idx_workspace_name" ON "workspaces" ("name");
-- Create index "idx_workspace_deleted_at" to table: "workspaces"
CREATE INDEX "idx_workspace_deleted_at" ON "workspaces" ("deleted_at");