-- Add query_input column to reasoner_history table
ALTER TABLE reasoner_history ADD COLUMN query_input VARCHAR(2000) NULL;
