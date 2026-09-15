-- Apply with a migration/admin role, never automatically with application credentials.
CREATE TABLE IF NOT EXISTS app_migrations(version text PRIMARY KEY, applied_at timestamptz NOT NULL DEFAULT now());
CREATE TABLE IF NOT EXISTS app_users(
 id bigserial PRIMARY KEY, identity_key text UNIQUE NOT NULL, display_name text NOT NULL DEFAULT '',
 disabled boolean NOT NULL DEFAULT false, created_at timestamptz NOT NULL DEFAULT now());
ALTER TABLE projects ADD COLUMN IF NOT EXISTS owner_id bigint REFERENCES app_users(id);
ALTER TABLE projects ALTER COLUMN owner_id SET DEFAULT nullif(current_setting('app.user_id', true), '')::bigint;
-- Legacy NULL owners remain unassigned. Administrators assign explicit project IDs only.
CREATE INDEX IF NOT EXISTS projects_owner_idx ON projects(owner_id);
ALTER TABLE projects ADD COLUMN IF NOT EXISTS electricity_rates text;
ALTER TABLE projects ADD COLUMN IF NOT EXISTS weather_station_name text;
ALTER TABLE projects ADD COLUMN IF NOT EXISTS weather_station_id text;
ALTER TABLE projects ADD COLUMN IF NOT EXISTS weather_station_distance numeric;
ALTER TABLE projects ADD COLUMN IF NOT EXISTS weather_station_latitude numeric;
ALTER TABLE projects ADD COLUMN IF NOT EXISTS weather_station_longitude numeric;
ALTER TABLE projects ADD COLUMN IF NOT EXISTS weather_station_elevation numeric;
ALTER TABLE building_elements ADD COLUMN IF NOT EXISTS name text;
ALTER TABLE building_elements ADD COLUMN IF NOT EXISTS element_code text;
ALTER TABLE building_elements ADD COLUMN IF NOT EXISTS wall_direction text;
ALTER TABLE element_radiation ADD COLUMN IF NOT EXISTS calculation_method text;
ALTER TABLE element_radiation ADD COLUMN IF NOT EXISTS calculated_at timestamptz;
ALTER TABLE radiation_analysis ADD COLUMN IF NOT EXISTS analysis_data text;
ALTER TABLE radiation_analysis ADD COLUMN IF NOT EXISTS total_annual_radiation numeric;
ALTER TABLE radiation_analysis ADD COLUMN IF NOT EXISTS total_elements integer;
ALTER TABLE optimization_results ADD COLUMN IF NOT EXISTS annual_energy_kwh numeric;
ALTER TABLE optimization_results ADD COLUMN IF NOT EXISTS selection_details jsonb;
ALTER TABLE optimization_results ALTER COLUMN roi TYPE numeric;
ALTER TABLE financial_analysis ALTER COLUMN irr TYPE numeric;
ALTER TABLE financial_analysis ALTER COLUMN npv TYPE numeric;
CREATE TABLE IF NOT EXISTS detailed_financial_analysis(
 id bigserial PRIMARY KEY, project_id integer REFERENCES projects(id),
 cash_flow_data text, sensitivity_data text, created_at timestamptz NOT NULL DEFAULT now());
CREATE TABLE IF NOT EXISTS step_completions(
 project_id integer REFERENCES projects(id),step_name text,completed_at timestamptz DEFAULT now(),
 completion_data text,PRIMARY KEY(project_id,step_name));
CREATE TABLE IF NOT EXISTS session_data(
 project_id integer REFERENCES projects(id),step_name text,data_key text,data_value text,
 updated_at timestamptz DEFAULT now(),PRIMARY KEY(project_id,step_name,data_key));
CREATE TABLE IF NOT EXISTS analysis_runs(
 id uuid PRIMARY KEY, project_id integer NOT NULL REFERENCES projects(id) ON DELETE RESTRICT,
 owner_id bigint NOT NULL REFERENCES app_users(id), run_type text NOT NULL, method text NOT NULL,
 model_version text NOT NULL, input_hash text NOT NULL, inputs jsonb NOT NULL, results jsonb NOT NULL,
 parent_run_id uuid REFERENCES analysis_runs(id), created_at timestamptz NOT NULL DEFAULT now());
CREATE INDEX IF NOT EXISTS analysis_runs_project_idx ON analysis_runs(project_id,created_at DESC);
CREATE OR REPLACE FUNCTION prevent_run_mutation() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN RAISE EXCEPTION 'Research runs are immutable; create a new run'; END $$;
DROP TRIGGER IF EXISTS immutable_analysis_runs ON analysis_runs;
CREATE TRIGGER immutable_analysis_runs BEFORE UPDATE OR DELETE ON analysis_runs
FOR EACH ROW EXECUTE FUNCTION prevent_run_mutation();
ALTER TABLE app_users ENABLE ROW LEVEL SECURITY;
ALTER TABLE app_users FORCE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS identity_policy ON app_users;
CREATE POLICY identity_policy ON app_users USING(identity_key=current_setting('app.identity_key',true))
 WITH CHECK(identity_key=current_setting('app.identity_key',true));
ALTER TABLE projects ENABLE ROW LEVEL SECURITY;
ALTER TABLE projects FORCE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS owner_policy ON projects;
CREATE POLICY owner_policy ON projects USING(owner_id=nullif(current_setting('app.user_id',true),'')::bigint)
 WITH CHECK(owner_id=nullif(current_setting('app.user_id',true),'')::bigint);
DO $$ DECLARE t record; BEGIN
 FOR t IN SELECT table_name FROM information_schema.columns
          WHERE table_schema=current_schema() AND column_name='project_id'
          AND table_name IN (SELECT tablename FROM pg_tables WHERE schemaname=current_schema()) LOOP
   EXECUTE format('ALTER TABLE %I ENABLE ROW LEVEL SECURITY',t.table_name);
   EXECUTE format('ALTER TABLE %I FORCE ROW LEVEL SECURITY',t.table_name);
   EXECUTE format('DROP POLICY IF EXISTS project_owner_policy ON %I',t.table_name);
   EXECUTE format('CREATE POLICY project_owner_policy ON %I USING
     (EXISTS(SELECT 1 FROM projects p WHERE p.id=project_id)) WITH CHECK
     (EXISTS(SELECT 1 FROM projects p WHERE p.id=project_id))',t.table_name);
 END LOOP;
 -- Views must evaluate policies as the caller, not a privileged view owner.
 FOR t IN SELECT table_name FROM information_schema.views WHERE table_schema=current_schema() LOOP
   EXECUTE format('ALTER VIEW %I SET (security_invoker=true)',t.table_name);
 END LOOP;
END $$;
INSERT INTO app_migrations(version) VALUES('002_multiuser') ON CONFLICT DO NOTHING;
DROP POLICY IF EXISTS run_author_policy ON analysis_runs;
CREATE POLICY run_author_policy ON analysis_runs AS RESTRICTIVE
 USING(owner_id=nullif(current_setting('app.user_id',true),'')::bigint)
 WITH CHECK(owner_id=nullif(current_setting('app.user_id',true),'')::bigint);

-- A parent run must belong to the same project, even for hand-written SQL.
CREATE UNIQUE INDEX IF NOT EXISTS analysis_runs_id_project_idx ON analysis_runs(id,project_id);
DO $$ BEGIN
 IF NOT EXISTS(SELECT 1 FROM pg_constraint WHERE conrelid='analysis_runs'::regclass AND conname='same_project_parent') THEN
  ALTER TABLE analysis_runs ADD CONSTRAINT same_project_parent
   FOREIGN KEY(parent_run_id,project_id) REFERENCES analysis_runs(id,project_id);
 END IF;
END $$;
