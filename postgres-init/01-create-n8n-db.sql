-- Auto-create the n8n database if it doesn't exist on first Postgres boot.
SELECT 'CREATE DATABASE n8n'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'n8n')\gexec
