import unittest
from unittest.mock import patch
import psycopg2
from services.authentication import Principal,bind_connection,current_principal
from services.run_store import append_run,list_runs,get_run
from tests.postgres_fixture import PostgresFixture

class OwnershipTests(PostgresFixture):
    def test_direct_sql_denies_foreign_project_reads_and_writes(self):
        other=Principal('https://test.example','user-b','B')
        with self.connect_as(other) as c:
            with c.cursor() as cur:
                cur.execute('SELECT id FROM projects');self.assertEqual(cur.fetchall(),[])
                cur.execute('UPDATE projects SET project_name=%s WHERE id=%s',('stolen',self.project_id));self.assertEqual(cur.rowcount,0)
                with self.assertRaises(psycopg2.errors.InsufficientPrivilege):
                    cur.execute('INSERT INTO historical_data(project_id,annual_consumption) VALUES(%s,10)',(self.project_id,))
        self.assertEqual(self.db.get_project_by_id(self.project_id)['project_name'],'Test project')

    def test_anonymous_and_unassigned_projects_are_hidden(self):
        with self.admin() as c:
            with c.cursor() as cur:
                cur.execute("INSERT INTO projects(project_name) VALUES('Legacy')")
                cur.execute('SET ROLE '+self.role)
                cur.execute('SELECT * FROM projects');self.assertEqual(cur.fetchall(),[])
        self.assertEqual(len(self.db.list_projects()),2)

    def test_runtime_role_cannot_disable_or_reenable_accounts(self):
        with self.connect() as c:
            with c.cursor() as cur:
                with self.assertRaises(psycopg2.errors.InsufficientPrivilege):
                    cur.execute('UPDATE app_users SET disabled=false')

    def test_suspended_account_and_privileged_role_fail_closed(self):
        with self.admin() as c:
            with c.cursor() as cur:cur.execute('UPDATE app_users SET disabled=true')
        with self.assertRaises(PermissionError):self.connect()
        with self.admin() as c:
            with self.assertRaises(PermissionError):bind_connection(c,self.principal)

    def test_immutable_runs_are_owned_and_retain_all_inputs(self):
        with self.connect() as c:
            run=append_run(c,self.project_id,'test','fixture',{'input':123},{'result':456},'v1')
        with self.connect() as c:
            self.assertEqual(get_run(c,run)['inputs'],{'input':123})
            self.assertEqual(len(list_runs(c,self.project_id)),1)
            with c.cursor() as cur:
                with self.assertRaises(psycopg2.errors.InsufficientPrivilege):cur.execute('DELETE FROM analysis_runs')
        with self.connect_as(Principal('https://test.example','user-b')) as c:
            self.assertIsNone(get_run(c,run))
        with self.admin() as c:
            with c.cursor() as cur:
                with self.assertRaises(psycopg2.errors.RaiseException):cur.execute('UPDATE analysis_runs SET method=\'altered\'')

    def test_project_save_with_foreign_id_never_creates_or_overwrites(self):
        with patch.object(self.db,'get_connection',lambda:self.connect_as(Principal('https://test.example','user-b'))),patch('database_manager.st.error'):
            self.assertIsNone(self.db.save_project({'project_id':self.project_id,'project_name':'stolen'}))
            self.assertEqual(self.db.list_projects(),[])

    def test_async_rebinding_cannot_reuse_the_previous_users_scope(self):
        import asyncio
        import asyncpg
        from tests.postgres_fixture import URL
        from services.authentication import bind_async_connection
        async def check():
            c=await asyncpg.connect(URL,server_settings={'search_path':self.schema})
            try:
                await c.execute('SET ROLE '+self.role)
                await bind_async_connection(c,self.principal)
                self.assertEqual(await c.fetchval('SELECT count(*) FROM projects'),2)
                await bind_async_connection(c,Principal('https://test.example','b'))
                self.assertEqual(await c.fetchval('SELECT count(*) FROM projects'),0)
                await c.execute('RESET ALL')
                self.assertEqual(await c.fetchval('SELECT count(*) FROM '+self.schema+'.projects'),0)
            finally:await c.close()
        asyncio.run(check())

    def test_parent_run_must_belong_to_the_same_project(self):
        with self.connect() as c:
            first=append_run(c,self.project_id,'fixture','fixture',{}, {},'v1')
        with self.connect() as c:
            with self.assertRaises(psycopg2.errors.ForeignKeyViolation):
                append_run(c,self.other_project_id,'fixture','fixture',{}, {},'v1',first)
