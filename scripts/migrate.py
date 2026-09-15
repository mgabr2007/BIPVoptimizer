"""Explicit additive migration runner. Does not assign legacy project owners."""
import os
from pathlib import Path
import psycopg2


def migrate(conn):
    root=Path(__file__).resolve().parents[1]
    with conn:
        with conn.cursor() as cur:
            cur.execute("SELECT pg_advisory_xact_lock(7152026)")
            cur.execute((root/'database_schema.sql').read_text())
            # PostgreSQL cannot widen financial columns while this view depends on them.
            # Preserve and restore the repository view in the same transaction. No CASCADE.
            cur.execute("SELECT pg_get_viewdef('project_report_view'::regclass,true)")
            view_sql=cur.fetchone()[0]
            cur.execute('DROP VIEW project_report_view')
            cur.execute((root/'migrations/002_multiuser.sql').read_text())
            cur.execute('CREATE VIEW project_report_view WITH (security_invoker=true) AS '+view_sql)


def grant_runtime(conn, role):
    """Grant data access, not schema ownership, migration writes or account admin."""
    from psycopg2 import sql
    with conn:
        with conn.cursor() as cur:
            cur.execute('SELECT rolsuper,rolbypassrls FROM pg_roles WHERE rolname=%s',(role,))
            row=cur.fetchone()
            if not row or any(row):raise ValueError('Runtime role must exist without SUPERUSER/BYPASSRLS')
            cur.execute('SELECT current_schema()');schema=cur.fetchone()[0]
            cur.execute(sql.SQL('GRANT USAGE ON SCHEMA {} TO {}').format(sql.Identifier(schema),sql.Identifier(role)))
            cur.execute(sql.SQL('GRANT SELECT,INSERT,UPDATE,DELETE ON ALL TABLES IN SCHEMA {} TO {}').format(sql.Identifier(schema),sql.Identifier(role)))
            cur.execute(sql.SQL('GRANT USAGE,SELECT ON ALL SEQUENCES IN SCHEMA {} TO {}').format(sql.Identifier(schema),sql.Identifier(role)))
            for table in ('app_migrations','app_users','analysis_runs'):
                cur.execute(sql.SQL('REVOKE ALL ON {} FROM {}').format(sql.Identifier(table),sql.Identifier(role)))
            cur.execute(sql.SQL('GRANT SELECT ON app_migrations TO {}').format(sql.Identifier(role)))
            cur.execute(sql.SQL('GRANT SELECT,INSERT ON analysis_runs TO {}').format(sql.Identifier(role)))
            cur.execute(sql.SQL('GRANT SELECT,INSERT(identity_key,display_name),UPDATE(display_name) ON app_users TO {}').format(sql.Identifier(role)))


if __name__=='__main__':
    import argparse
    from contextlib import closing
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runtime-role',required=True,help='Existing nonprivileged application login role')
    args=parser.parse_args()
    # Migration credentials are separate from the application DATABASE_URL.
    with closing(psycopg2.connect(os.environ['BIPV_MIGRATION_DATABASE_URL'])) as conn:
        migrate(conn)
        grant_runtime(conn,args.runtime_role)
    print('Migration and runtime grants complete. Legacy projects remain unassigned.')
