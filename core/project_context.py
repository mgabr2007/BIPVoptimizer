"""Resolve explicit project selection without selecting another database record.

This is selection hygiene, not an authorization boundary. Multi-user access still
requires ownership checks in the application's data-access layer.
"""


def selected_project_id(state):
    project = state.get('project_data') or {}
    candidates = [state.get('project_id'), project.get('project_id'), project.get('id')]
    ids = set()
    for value in candidates:
        if value is None:
            continue
        if isinstance(value, bool) or not str(value).isdigit() or int(value) <= 0:
            return None
        ids.add(int(value))
    return ids.pop() if len(ids) == 1 else None
