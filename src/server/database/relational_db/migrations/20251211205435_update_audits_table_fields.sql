-- Modify "audits" table
ALTER TABLE "audits" ALTER COLUMN "audit_resource_id" DROP NOT NULL, ALTER COLUMN "created_by_user_id" DROP NOT NULL, ALTER COLUMN "updated_by_user_id" DROP NOT NULL, ADD COLUMN "deleted_bu_user_id" character varying(36) NULL;
