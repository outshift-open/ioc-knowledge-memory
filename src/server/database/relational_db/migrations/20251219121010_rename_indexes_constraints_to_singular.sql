-- Rename indexes and foreign key constraints to match singular table names

-- Reasoner indexes
ALTER INDEX IF EXISTS "idx_reasoners_workspace_id" RENAME TO "idx_reasoner_workspace_id";
ALTER INDEX IF EXISTS "idx_reasoners_mas_id" RENAME TO "idx_reasoner_mas_id";
ALTER INDEX IF EXISTS "idx_reasoners_deleted_at" RENAME TO "idx_reasoner_deleted_at";
ALTER INDEX IF EXISTS "idx_reasoners_workspace_name_unique" RENAME TO "idx_reasoner_workspace_name_unique";

-- User indexes
ALTER INDEX IF EXISTS "idx_users_deleted_at" RENAME TO "idx_user_deleted_at";

-- Audit indexes
ALTER INDEX IF EXISTS "idx_audits_audit_resource_id" RENAME TO "idx_audit_audit_resource_id";
ALTER INDEX IF EXISTS "idx_audits_deleted_at" RENAME TO "idx_audit_deleted_at";
ALTER INDEX IF EXISTS "idx_audits_request_id" RENAME TO "idx_audit_request_id";

-- Foreign key constraints 
-- Reasoner FKs 
ALTER TABLE "reasoner" RENAME CONSTRAINT "fk_reasoners_workspace" TO "fk_reasoner_workspace";
ALTER TABLE "reasoner" RENAME CONSTRAINT "fk_reasoners_mas" TO "fk_reasoner_mas";

-- MAS FK 
ALTER TABLE "multi_agentic_system" RENAME CONSTRAINT "fk_mas_workspace" TO "fk_multi_agentic_system_workspace";

-- KEP FK 
ALTER TABLE "knowledge_adapter" RENAME CONSTRAINT "fk_kep_workspace" TO "fk_knowledge_adapter_workspace";

