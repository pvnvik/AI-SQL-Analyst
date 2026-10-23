-- ==============================================================================
-- QueryPilot — PostgreSQL Read-Only Role & Permission Configuration
-- ==============================================================================
-- This script sets up the least-privilege 'querypilot_readonly' role.
-- It grants CONNECT, USAGE, and SELECT on approved analytical tables ONLY.
--
-- Usage (run as superuser or database owner, e.g. postgres):
--   psql -U postgres -d querypilot -f setup_permissions.sql
-- ==============================================================================

-- 1. Create database if it does not exist (run in postgres database first)
-- CREATE DATABASE querypilot;

-- 2. Create the dedicated read-only role with a secure password
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'querypilot_readonly') THEN
        CREATE ROLE querypilot_readonly WITH LOGIN PASSWORD 'change_me_to_strong_password';
    END IF;
END
$$;

-- 3. Revoke all default public permissions
REVOKE ALL ON DATABASE querypilot FROM querypilot_readonly;
REVOKE CREATE ON SCHEMA public FROM querypilot_readonly;

-- 4. Grant connection to the database
GRANT CONNECT ON DATABASE querypilot TO querypilot_readonly;

-- 5. Grant USAGE on public schema (necessary to resolve table names)
GRANT USAGE ON SCHEMA public TO querypilot_readonly;

-- 6. Grant SELECT ONLY on approved analytical tables
GRANT SELECT ON TABLE customers TO querypilot_readonly;
GRANT SELECT ON TABLE products TO querypilot_readonly;
GRANT SELECT ON TABLE orders TO querypilot_readonly;
GRANT SELECT ON TABLE order_items TO querypilot_readonly;

-- 7. Ensure future tables do not automatically grant write privileges
ALTER DEFAULT PRIVILEGES IN SCHEMA public REVOKE ALL ON TABLES FROM querypilot_readonly;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO querypilot_readonly;

-- 8. Enforce statement timeout directly at role level (10 seconds = 10000ms)
ALTER ROLE querypilot_readonly SET statement_timeout = '10s';

-- 9. Explicitly ensure write permissions are NEVER granted
REVOKE INSERT, UPDATE, DELETE, TRUNCATE, REFERENCES, TRIGGER ON ALL TABLES IN SCHEMA public FROM querypilot_readonly;

COMMENT ON ROLE querypilot_readonly IS 'Restricted read-only role for QueryPilot agentic SQL execution';
