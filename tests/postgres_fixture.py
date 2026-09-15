from contextlib import closing
import os
import unittest
import uuid
from urllib.parse import urlparse
import psycopg2
from psycopg2 import sql
from scripts.migrate import migrate,grant_runtime
from services.authentication import bind_connection,Principal
from database_manager import BIPVDatabaseManager

URL=os.getenv('BIPV_TEST_DATABASE_URL')

class PostgresFixture(unittest.TestCase):
    def setUp(self):
        if not URL:self.skipTest('BIPV_TEST_DATABASE_URL not configured')
        if urlparse(URL).hostname not in ('localhost','127.0.0.1'):self.fail('Loopback test DB required')
        suffix=uuid.uuid4().hex
        self.schema='bipv_'+suffix;self.role='runtime_'+suffix
        self.principal=Principal('https://test.example','user-a','A')
        with psycopg2.connect(URL) as c:
            with c.cursor() as cur:
                cur.execute(sql.SQL('CREATE SCHEMA {}').format(sql.Identifier(self.schema)))
                cur.execute(sql.SQL('CREATE ROLE {} NOLOGIN NOSUPERUSER NOBYPASSRLS').format(sql.Identifier(self.role)))
        self.addCleanup(self.cleanup_database)
        with closing(self.admin()) as c:
            migrate(c);grant_runtime(c,self.role)
        self.db=BIPVDatabaseManager();self.db.get_connection=self.connect
        self.project_id=self.db.save_project({'project_name':'Test project','location':'Berlin'})
        self.assertIsNotNone(self.project_id)
        self.other_project_id=self.db.save_project({'project_name':'Other project','location':'Berlin'})

    def admin(self):
        return psycopg2.connect(URL,options=f'-c search_path={self.schema}')

    def connect_as(self,principal):
        c=self.admin()
        try:
            with c.cursor() as cur:cur.execute(sql.SQL('SET ROLE {}').format(sql.Identifier(self.role)))
            bind_connection(c,principal)
            return c
        except Exception:
            c.close();raise

    def connect(self):return self.connect_as(self.principal)

    def cleanup_database(self):
        with self.admin() as c:
            with c.cursor() as cur:
                cur.execute(sql.SQL('DROP SCHEMA {} CASCADE').format(sql.Identifier(self.schema)))
                cur.execute(sql.SQL('DROP ROLE {}').format(sql.Identifier(self.role)))
