-- Run this in DBeaver to create schema and contacts table
-- Connection: postgresql://postgres:123456@localhost:5432/postgres

-- 1. Create schema
CREATE SCHEMA IF NOT EXISTS kosam_uat;

-- 2. Create contacts table in kosam_uat schema
CREATE TABLE IF NOT EXISTS kosam_uat.contacts (
    id SERIAL PRIMARY KEY,
    name VARCHAR NOT NULL,
    email VARCHAR UNIQUE,
    phone VARCHAR,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 3. Create index on email (for faster lookups)
CREATE INDEX IF NOT EXISTS ix_kosam_uat_contacts_email ON kosam_uat.contacts(email);
CREATE INDEX IF NOT EXISTS ix_kosam_uat_contacts_id ON kosam_uat.contacts(id);

-- 4. Verify - list tables in schema
SELECT table_schema, table_name 
FROM information_schema.tables 
WHERE table_schema = 'kosam_uat';
