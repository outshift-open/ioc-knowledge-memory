-- Modify "software" table
ALTER TABLE "software" DROP COLUMN "sw_type", ADD COLUMN "type" character varying(60) NOT NULL;
