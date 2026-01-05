-- Rename tables from plural to singular
ALTER TABLE "workspaces" RENAME TO "workspace";
ALTER TABLE "multi_agentic_systems" RENAME TO "multi_agentic_system";
ALTER TABLE "reasoners" RENAME TO "reasoner";
ALTER TABLE "knowledge_adapters" RENAME TO "knowledge_adapter";
ALTER TABLE "users" RENAME TO "user";
ALTER TABLE "audits" RENAME TO "audit";

