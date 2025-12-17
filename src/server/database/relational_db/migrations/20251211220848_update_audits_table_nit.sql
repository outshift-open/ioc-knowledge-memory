-- Rename a column from "deleted_bu_user_id" to "deleted_by"
ALTER TABLE "audits" RENAME COLUMN "deleted_bu_user_id" TO "deleted_by_user_id";
-- Modify "audits" table
ALTER TABLE "audits" ALTER COLUMN "audit_resource_id" TYPE character varying(360);
