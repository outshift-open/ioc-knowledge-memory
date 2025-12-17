-- Create "reasoners" table
CREATE TABLE "reasoners" (
  "id" character varying(36) NOT NULL DEFAULT (gen_random_uuid())::text,
  "workspace_id" character varying(36) NOT NULL,
  "mas_id" character varying(36) NOT NULL,
  "name" character varying(255) NOT NULL,
  "config" jsonb NULL,
  "created_at" timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updated_at" timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  "created_by" character varying(255) NULL,
  "updated_by" character varying(255) NULL,
  "deleted_at" timestamp NULL,
  PRIMARY KEY ("id")
);

-- Create index "idx_reasoners_workspace_id" to table: "reasoners"
CREATE INDEX "idx_reasoners_workspace_id" ON "reasoners" ("workspace_id");

-- Create index "idx_reasoners_mas_id" to table: "reasoners"
CREATE INDEX "idx_reasoners_mas_id" ON "reasoners" ("mas_id");

-- Create index "idx_reasoners_deleted_at" to table: "reasoners"
CREATE INDEX "idx_reasoners_deleted_at" ON "reasoners" ("deleted_at");

-- Create unique index on name within workspace (excluding soft-deleted records)
CREATE UNIQUE INDEX "idx_reasoners_workspace_name_unique" ON "reasoners" ("workspace_id", "name") WHERE "deleted_at" IS NULL;
