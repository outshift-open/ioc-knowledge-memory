-- Create "software" table
CREATE TABLE "software" (
  "id" character varying(36) NOT NULL DEFAULT (gen_random_uuid())::text,
  "type" character varying(60) NOT NULL,
  "name" character varying(60) NOT NULL,
  "workspace_id" character varying(36) NOT NULL,
  "config" json NULL,
  "created_at" timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updated_at" timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  "deleted_at" timestamp NULL,
  PRIMARY KEY ("id")
);
