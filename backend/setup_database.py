import os
import sys
from supabase import create_client, Client

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config

def setup_database():
    """Setup database tables"""
    
    try:
        # Initialize Supabase client
        supabase: Client = create_client(Config.SUPABASE_URL, Config.SUPABASE_SERVICE_KEY)
        
        # SQL for creating videos table
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS videos (
            id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
            original_filename VARCHAR(255) NOT NULL,
            file_path TEXT NOT NULL,
            processed_path TEXT,
            storage_url TEXT,
            source_url TEXT,
            source_type VARCHAR(50),
            platform VARCHAR(50),
            file_size BIGINT,
            duration FLOAT,
            thumbnail_url TEXT,
            status VARCHAR(50) DEFAULT 'uploaded',
            processing_options JSONB,
            ai_analysis JSONB,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()),
            processed_at TIMESTAMP WITH TIME ZONE,
            user_id UUID,
            tags TEXT[],
            metadata JSONB
        );
        
        -- Create indexes
        CREATE INDEX IF NOT EXISTS idx_videos_status ON videos(status);
        CREATE INDEX IF NOT EXISTS idx_videos_created_at ON videos(created_at DESC);
        CREATE INDEX IF NOT EXISTS idx_videos_user_id ON videos(user_id);
        
        -- Create processing_jobs table
        CREATE TABLE IF NOT EXISTS processing_jobs (
            id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
            video_id UUID REFERENCES videos(id) ON DELETE CASCADE,
            task_id VARCHAR(100) UNIQUE,
            status VARCHAR(50) DEFAULT 'pending',
            progress INTEGER DEFAULT 0,
            message TEXT,
            options JSONB,
            result JSONB,
            error TEXT,
            started_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()),
            completed_at TIMESTAMP WITH TIME ZONE,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW())
        );
        
        CREATE INDEX IF NOT EXISTS idx_processing_jobs_task_id ON processing_jobs(task_id);
        CREATE INDEX IF NOT EXISTS idx_processing_jobs_status ON processing_jobs(status);
        CREATE INDEX IF NOT EXISTS idx_processing_jobs_video_id ON processing_jobs(video_id);
        
        -- Create storage bucket if not exists
        INSERT INTO storage.buckets (id, name, public)
        VALUES ('video-storage', 'video-storage', true)
        ON CONFLICT (id) DO NOTHING;
        
        -- Set up storage policies
        CREATE POLICY "Public Access" ON storage.objects
        FOR SELECT USING (bucket_id = 'video-storage');
        
        CREATE POLICY "Authenticated users can upload" ON storage.objects
        FOR INSERT WITH CHECK (
            bucket_id = 'video-storage' 
            AND auth.role() = 'authenticated'
        );
        
        CREATE POLICY "Users can update own files" ON storage.objects
        FOR UPDATE USING (
            bucket_id = 'video-storage' 
            AND auth.uid() = owner
        );
        
        CREATE POLICY "Users can delete own files" ON storage.objects
        FOR DELETE USING (
            bucket_id = 'video-storage' 
            AND auth.uid() = owner
        );
        """
        
        # Execute SQL using Supabase's REST API
        # Note: Supabase doesn't directly execute raw SQL via Python client
        # This is a simplified approach - in production, use migrations
        print("Database setup completed. Please run SQL manually in Supabase SQL editor:")
        print("\nSQL to execute:")
        print("=" * 80)
        print(create_table_sql)
        print("=" * 80)
        
        print("\n✅ Database setup instructions generated.")
        print("Please run the above SQL in your Supabase dashboard at:")
        print(f"{Config.SUPABASE_URL}/project/_/sql")
        
    except Exception as e:
        print(f"❌ Error setting up database: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    setup_database()