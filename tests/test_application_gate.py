import time
import unittest
from unittest.mock import patch
from streamlit.testing.v1 import AppTest
from services.authentication import Principal,current_principal

class Claims(dict):
    @property
    def is_logged_in(self):return self.get('logged_in',False)

class AccountGateTests(unittest.TestCase):
    def test_logged_out_app_does_not_read_projects(self):
        with patch('database_manager.db_manager.get_connection',side_effect=AssertionError('Data read before sign-in')):
            app=AppTest.from_file('app.py').run(timeout=20)
        self.assertFalse(app.exception,str(app.exception))
        self.assertTrue(any('Sign in' in element.value for element in app.markdown))

    def test_missing_expired_and_unverified_claims_are_denied(self):
        for claims in [Claims(),Claims(logged_in=True,sub='a'),Claims(logged_in=True,iss='https://idp',sub='a',exp=time.time()-1)]:
            with patch('services.authentication.st.user',claims),self.assertRaises(PermissionError):current_principal()
        with patch('services.authentication.st.user',Claims(logged_in=True,iss='https://idp',sub='a')):
            self.assertEqual(current_principal().key,Principal('https://idp','a').key)
        self.assertNotEqual(Principal('https://idp','a').key,Principal('https://other','a').key)

    def test_authenticated_application_loads_research_navigation(self):
        principal=Principal('https://idp','a')
        claims=Claims(logged_in=True,iss=principal.issuer,sub=principal.subject,name='Researcher')
        with patch('services.authentication.st.user',claims),patch('database_manager.db_manager.list_projects',return_value=[]):
            app=AppTest.from_file('app.py')
            app.query_params['step']='research_validation'
            app.run(timeout=20)
        self.assertFalse(app.exception,str(app.exception))
        self.assertTrue(any('Research validation' in element.value for element in app.header))
