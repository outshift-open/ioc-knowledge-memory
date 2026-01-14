-- Create "reasoner_history" table for storing query history
CREATE TABLE "reasoner_history" (
  "id" character varying(36) NOT NULL DEFAULT (gen_random_uuid())::text,
  "workspace_id" character varying(36) NOT NULL,
  "reasoner_id" character varying(36) NOT NULL,
  "request_id" character varying(255) NULL,
  "response_id" character varying(255) NULL,
  "response_data" jsonb NOT NULL,
  "created_at" timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "created_by" character varying(255) NULL,
  PRIMARY KEY ("id"),
  FOREIGN KEY ("workspace_id") REFERENCES "workspace" ("id"),
  FOREIGN KEY ("reasoner_id") REFERENCES "reasoner" ("id")
);

-- Create index "idx_reasoner_history_workspace_id" to table: "reasoner_history"
CREATE INDEX "idx_reasoner_history_workspace_id" ON "reasoner_history" ("workspace_id");

-- Create index "idx_reasoner_history_reasoner_id" to table: "reasoner_history"
CREATE INDEX "idx_reasoner_history_reasoner_id" ON "reasoner_history" ("reasoner_id");

-- Create index "idx_reasoner_history_created_at" to table: "reasoner_history"
CREATE INDEX "idx_reasoner_history_created_at" ON "reasoner_history" ("created_at");
