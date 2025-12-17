-- Rename a column from "created_by_user_id" to "created_by"
ALTER TABLE "audits" RENAME COLUMN "created_by_user_id" TO "created_by";
-- Rename a column from "updated_by_user_id" to "updated_by"
ALTER TABLE "audits" RENAME COLUMN "updated_by_user_id" TO "updated_by";
-- Rename a column from "deleted_by_user_id" to "deleted_by"
ALTER TABLE "audits" RENAME COLUMN "deleted_by_user_id" TO "deleted_by";
