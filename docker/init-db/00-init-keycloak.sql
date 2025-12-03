-- =============================================================================
-- PEA RE Forecast Platform - Keycloak Database Initialization
-- This script creates the keycloak database for authentication
-- =============================================================================

-- Create keycloak database if it doesn't exist
-- Note: This runs as postgres superuser during container initialization
SELECT 'CREATE DATABASE keycloak'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'keycloak')\gexec

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE keycloak TO postgres;
