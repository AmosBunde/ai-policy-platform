-- Bootstrap: extensions only.
--
-- The schema is owned by alembic (services/gateway-service/alembic/):
--   001_initial_schema  — tables + indexes
--   002_triggers_rls    — updated_at/audit triggers, RLS policies
-- Apply with:  make migrate     (docker compose exec gateway-service alembic upgrade head)
-- Seed with:   make seed        (scripts/seed_data.py — idempotent; admin
--                                password comes from SEED_ADMIN_PASSWORD)
--
-- Do NOT add tables, triggers, or seed rows here — they will drift from the
-- migrations and from the ORM models in shared/models/orm.py.

CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
