import unittest
from core.project_context import selected_project_id


class ProjectContextTests(unittest.TestCase):
    def test_no_implicit_selection(self):
        self.assertIsNone(selected_project_id({}))
        self.assertIsNone(selected_project_id({'current_project_id': 9}))
        self.assertIsNone(selected_project_id({'project_name': 'Some project'}))

    def test_explicit_and_consistent_ids(self):
        self.assertEqual(selected_project_id({'project_id': '3', 'project_data': {'id': 3}}), 3)
        self.assertEqual(selected_project_id({'project_data': {'project_id': 4}}), 4)

    def test_conflicting_or_invalid_ids_fail_closed(self):
        self.assertIsNone(selected_project_id({'project_id': 3, 'project_data': {'id': 4}}))
        for value in (True, -1, 0, 'abc', 1.5):
            self.assertIsNone(selected_project_id({'project_id': value}))
