-- Create "audits" table
CREATE TABLE "audits" (
  "id" character varying(36) NOT NULL DEFAULT (gen_random_uuid())::text,
  "request_id" character varying(36) NULL,
  "resource_type" character varying(360) NOT NULL,
  "audit_type" character varying(360) NOT NULL,
  "audit_resource_id" character varying(36) NOT NULL,
  "created_by_user_id" character varying(36) NOT NULL,
  "updated_by_user_id" character varying(36) NOT NULL,
  "created_at" timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updated_at" timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  "deleted_at" timestamp NULL,
  PRIMARY KEY ("id")
);
-- Create index "idx_audits_audit_resource_id" to table: "audits"
CREATE INDEX "idx_audits_audit_resource_id" ON "audits" ("audit_resource_id");
-- Create index "idx_audits_deleted_at" to table: "audits"
CREATE INDEX "idx_audits_deleted_at" ON "audits" ("deleted_at");
-- Create index "idx_audits_request_id" to table: "audits"
CREATE INDEX "idx_audits_request_id" ON "audits" ("request_id");
