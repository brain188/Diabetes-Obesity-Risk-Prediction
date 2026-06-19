-- docker/postgres/init.sql
-- PostgreSQL initialization script

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Create schemas if needed
-- CREATE SCHEMA IF NOT EXISTS dss;

-- Set default privileges
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO dss_user;

-- Create application user
-- (Already created via environment variables)

-- Set timezone
SET timezone = 'UTC';

-- Configure settings
ALTER SYSTEM SET max_connections = 100;
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '768MB';
ALTER SYSTEM SET maintenance_work_mem = '64MB';
ALTER SYSTEM SET checkpoint_completion_target = 0.9;
ALTER SYSTEM SET wal_buffers = '16MB';
ALTER SYSTEM SET default_statistics_target = 100;

-- Reload configuration
SELECT pg_reload_conf();

-- Create audit table for triggers (optional)
-- CREATE TABLE IF NOT EXISTS audit.log_entries (
--     id BIGSERIAL PRIMARY KEY,
--     table_name TEXT NOT NULL,
--     operation TEXT NOT NULL,
--     old_data JSONB,
--     new_data JSONB,
--     changed_by TEXT,
--     changed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
-- );

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE dss_db TO dss_user;

-- Log successful initialization
RAISE NOTICE 'PostgreSQL initialization complete!';