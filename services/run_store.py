"""Append-only research evidence; writes participate in the caller's transaction."""
import hashlib
import json
import uuid
from psycopg2.extras import RealDictCursor


def json_value(value):
    if hasattr(value,'to_dict') and hasattr(value,'columns'):
        return json_value(value.to_dict('records'))
    if isinstance(value,dict):
        return {str(k):json_value(v) for k,v in value.items()}
    if isinstance(value,(list,tuple)):
        return [json_value(v) for v in value]
    if hasattr(value,'tolist'):
        return json_value(value.tolist())
    return value


def canonical(value):
    return json.dumps(json_value(value),sort_keys=True,default=str,allow_nan=False,separators=(',',':'))


def append_run(conn, project_id, run_type, method, inputs, results, model_version, parent_run_id=None):
    with conn.cursor() as cur:
        cur.execute('SELECT owner_id FROM projects WHERE id=%s',(project_id,))
        row=cur.fetchone()
        if not row or row[0] is None:
            raise PermissionError('Project not found, unassigned or access denied')
        encoded=canonical(inputs)
        run_id=str(uuid.uuid4())
        cur.execute('''INSERT INTO analysis_runs
                    (id,project_id,owner_id,run_type,method,model_version,input_hash,inputs,results,parent_run_id)
                    VALUES(%s,%s,%s,%s,%s,%s,%s,%s::jsonb,%s::jsonb,%s)''',
                    (run_id,project_id,row[0],run_type,method,model_version,
                     hashlib.sha256(encoded.encode()).hexdigest(),encoded,canonical(results),parent_run_id))
        return run_id


def archive_legacy_before_replacement(conn, project_id, kind):
    """Preserve the last unversioned current rows once, before first replacement."""
    tables={'optimization':('optimization_results',),
            'financial':('financial_analysis','detailed_financial_analysis','environmental_impact')}
    with conn.cursor() as cur:
        cur.execute('SELECT 1 FROM analysis_runs WHERE project_id=%s AND run_type=%s LIMIT 1',(project_id,kind))
        if cur.fetchone():
            return
        snapshot={}
        for table in tables[kind]:
            # Table names come only from the fixed mapping above.
            cur.execute(f'SELECT coalesce(jsonb_agg(to_jsonb(t)),\'[]\'::jsonb) FROM {table} t WHERE project_id=%s',(project_id,))
            snapshot[table]=cur.fetchone()[0]
        if any(snapshot.values()):
            append_run(conn,project_id,kind,'legacy-unverified',{},snapshot,'legacy-unknown')


def list_runs(conn,project_id):
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute('''SELECT id,run_type,method,model_version,input_hash,parent_run_id,created_at
                       FROM analysis_runs WHERE project_id=%s ORDER BY created_at DESC,id''',(project_id,))
        return [dict(r) for r in cur.fetchall()]


def get_run(conn,run_id):
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute('SELECT * FROM analysis_runs WHERE id=%s',(run_id,))
        row=cur.fetchone()
        return dict(row) if row else None
