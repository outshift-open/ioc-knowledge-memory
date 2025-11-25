-- Create "software" table
CREATE TABLE "software" (
  "id" character varying(36) NOT NULL DEFAULT (gen_random_uuid())::text,
  "type" character varying(180) NOT NULL,
  "config" json NULL,
  "created_at" timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updated_at" timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  "deleted_at" timestamp NULL,
  PRIMARY KEY ("id")
);
-- Create index "idx_software_deleted_at" to table: "software"
CREATE INDEX "idx_software_deleted_at" ON "software" ("deleted_at");
-- Create index "idx_software_type" to table: "software"
CREATE INDEX "idx_software_type" ON "software" ("type");
