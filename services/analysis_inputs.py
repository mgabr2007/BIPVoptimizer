"""Read-only input snapshot shared by optimization and financial cache checks."""
def upstream_snapshot(db, project_id):
    data = {'pv': db.get_pv_specifications(project_id),
            'historical': db.get_historical_data(project_id),
            'radiation': db.get_radiation_analysis_data(project_id),
            'project': db.get_project_by_id(project_id)}
    if any(value is None for value in data.values()):
        raise ValueError('Upstream inputs could not be loaded; analysis cannot be associated with a complete input snapshot')
    return data
