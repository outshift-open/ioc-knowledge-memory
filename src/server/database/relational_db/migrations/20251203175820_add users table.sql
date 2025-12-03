-- Create "users" table
CREATE TABLE "users" (
  "id" character varying(36) NOT NULL DEFAULT (gen_random_uuid())::text,
  "username" character varying(360) NOT NULL,
  "password" character varying(360) NOT NULL,
  "domain" character varying(360) NOT NULL,
  "role" character varying(360) NOT NULL,
  "created_at" timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updated_at" timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  "deleted_at" timestamp NULL,
  PRIMARY KEY ("id")
);
-- Create index "idx_users_deleted_at" to table: "users"
CREATE INDEX "idx_users_deleted_at" ON "users" ("deleted_at");
