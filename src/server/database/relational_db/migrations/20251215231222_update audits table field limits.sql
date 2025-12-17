-- Modify "audits" table
ALTER TABLE "audits" ALTER COLUMN "created_by_user_id" TYPE character varying(360), ALTER COLUMN "updated_by_user_id" TYPE character varying(360), ALTER COLUMN "deleted_by_user_id" TYPE character varying(360);
-- Create "tkf" table
CREATE TABLE "tkf" (
  "id" character varying(36) NOT NULL DEFAULT (gen_random_uuid())::text,
  "type" character varying(360) NOT NULL,
  "wksp_id" character varying(36) NULL,
  "mas_id" character varying(36) NULL,
  "memory_type" character varying(36) NULL,
  "created_at" timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updated_at" timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  "deleted_at" timestamp NULL,
  PRIMARY KEY ("id")
);
-- Create index "idx_tkf_deleted_at" to table: "tkf"
CREATE INDEX "idx_tkf_deleted_at" ON "tkf" ("deleted_at");
