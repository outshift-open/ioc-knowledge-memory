-- Create "knowledge_adapters" table
CREATE TABLE "knowledge_adapters" (
  "id" character varying(36) NOT NULL DEFAULT (gen_random_uuid())::text,
  "workspace_id" character varying(36) NOT NULL,
  "name" character varying(255) NOT NULL,
  "mas_ids" jsonb NOT NULL,
  "type" character varying(50) NOT NULL,
  "software_type" character varying(90) NOT NULL,
  "software_config" jsonb NULL,
  "created_at" timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updated_at" timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  "created_by" character varying(255) NULL,
  "updated_by" character varying(255) NULL,
  "deleted_at" timestamp NULL,
  PRIMARY KEY ("id")
);
-- Create index "idx_kep_workspace_id" to table: "knowledge_adapters"
CREATE INDEX "idx_kep_workspace_id" ON "knowledge_adapters" ("workspace_id");
-- Create index "idx_kep_software_type" to table: "knowledge_adapters"
CREATE INDEX "idx_kep_software_type" ON "knowledge_adapters" ("software_type");
-- Create index "idx_kep_deleted_at" to table: "knowledge_adapters"
CREATE INDEX "idx_kep_deleted_at" ON "knowledge_adapters" ("deleted_at");
-- Create unique index on name within workspace (excluding soft-deleted records)
CREATE UNIQUE INDEX "idx_kep_workspace_name_unique" ON "knowledge_adapters" ("workspace_id", "name") WHERE "deleted_at" IS NULL;
