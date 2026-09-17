"""Explicit admin-only mapping of an unassigned legacy project to an OIDC identity."""
import argparse
import hashlib
import json
import os
import psycopg2


def assign(conn,project_id,issuer,subject):
    identity=hashlib.sha256(json.dumps([issuer,subject],separators=(',',':')).encode()).hexdigest()
    with conn.cursor() as cur:
        cur.execute('INSERT INTO app_users(identity_key) VALUES(%s) ON CONFLICT DO NOTHING',(identity,))
        cur.execute('''UPDATE projects SET owner_id=(SELECT id FROM app_users WHERE identity_key=%s)
                       WHERE id=%s AND owner_id IS NULL RETURNING id''',(identity,project_id))
        if cur.fetchone() is None:raise ValueError('Project does not exist or already has an owner')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project-id',type=int,required=True)
    parser.add_argument('--issuer',required=True)
    parser.add_argument('--subject',required=True)
    args=parser.parse_args()
    with psycopg2.connect(os.environ['BIPV_MIGRATION_DATABASE_URL']) as conn:
        assign(conn,args.project_id,args.issuer,args.subject)
    print('Explicit legacy project ownership assigned.')
