-- Modify "software" table
ALTER TABLE "software" DROP COLUMN "type", ADD COLUMN "sw_type" character varying(60) NOT NULL;
