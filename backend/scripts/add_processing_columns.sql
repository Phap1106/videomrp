-- Add columns used by recent releases (safe to run multiple times)
ALTER TABLE IF EXISTS video_jobs
ADD COLUMN IF NOT EXISTS processing_flow VARCHAR(50) DEFAULT 'auto';

-- For Postgres use JSONB
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'video_jobs' AND column_name = 'processing_options'
    ) THEN
        ALTER TABLE video_jobs ADD COLUMN processing_options JSONB NULL;
    END IF;
END$$;