-- Rename a column from "status" to "audit_information"
ALTER TABLE "audits" RENAME COLUMN "status" TO "audit_information";
-- Modify "audits" table
ALTER TABLE "audits" ADD COLUMN "audit_extra_information" text NULL;
