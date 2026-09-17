"""Owned, immutable analysis history and portable evidence export."""
import streamlit as st
import pandas as pd
from database_manager import db_manager
from services.io import get_current_project_id
from services.run_store import list_runs,get_run,canonical


def render_run_history():
    st.header('Analysis run history')
    project_id=get_current_project_id()
    if not project_id:
        st.info('Select a project first.')
        return
    conn=db_manager.get_connection()
    if not conn:return
    try:
        runs=list_runs(conn,project_id)
        if not runs:
            st.info('No saved research runs yet.')
            return
        st.dataframe(pd.DataFrame(runs),hide_index=True)
        run_id=st.selectbox('Inspect a run',[str(r['id']) for r in runs])
        run=get_run(conn,run_id)
        if run:
            st.json({'method':run['method'],'model_version':run['model_version'],
                     'input_hash':run['input_hash'],'created_at':str(run['created_at'])})
            st.download_button('Download complete run evidence',canonical(run),
                               file_name=f'bipv-run-{run_id}.json',mime='application/json')
            with st.expander('Inputs and results'):
                st.json(canonical({'inputs':run['inputs'],'results':run['results']}))
    finally:conn.close()
