"""User-supplied research evidence, evaluated explicitly and archived by project."""
import streamlit as st
import pandas as pd
import pvlib
from database_manager import db_manager
from services.io import get_current_project_id
from services.run_store import append_run,canonical
from core.financial_scenario import create_cash_flow_analysis,input_fingerprint
from core.financial_math import calculate_npv,calculate_irr,calculate_payback_period
from core.time_series_research import (matched_balance,pv_profile,validation_metrics,interval_frame,
                                        BALANCE_VERSION,PHYSICS_VERSION)
from core.evaluated_forecast import evaluate_forecast,VERSION as FORECAST_VERSION


def render_research_validation():
    st.header('Research validation')
    project_id=get_current_project_id()
    if not project_id:
        st.info('Select a project first.');return
    mode=st.selectbox('Research study',['Time-matched energy and finance','PV model and measured comparison','Forecast holdout evaluation'])
    st.caption('Each saved study preserves its complete uploaded input, assumptions and output in Run History. These studies do not silently replace the annual optimization scenario.')
    params={}
    if mode.startswith('Time'):
        st.write('Upload a complete UTC calendar year: timestamp, generation_kwh, demand_kwh. Each row is an interval starting at the timestamp, with timezone offsets, regular intervals of at most one hour and no gaps. This model has no storage or curtailment.')
        params['electricity_price']=st.number_input('Import tariff (€/kWh)',min_value=0.,value=.30)
        params['export_rate']=st.number_input('Export tariff (€/kWh)',min_value=0.,value=.08)
        params['cost']=st.number_input('Investment represented by this generation profile (€)',min_value=0.,value=10000.)
        params['lifetime']=st.number_input('Financial lifetime (years)',min_value=1,max_value=50,value=25)
        params['discount']=st.number_input('Discount rate (fraction)',min_value=0.,max_value=1.,value=.05)
        params['system_degradation']=st.number_input('Annual generation degradation (fraction)',min_value=0.,max_value=.2,value=.005,format='%.3f')
        params['maintenance_cost_rate']=st.number_input('Annual maintenance / investment (fraction)',min_value=0.,max_value=1.,value=.015,format='%.3f')
        params['price_escalation']=st.number_input('Annual escalation of both tariffs (fraction)',min_value=0.,max_value=1.,value=.02)
        params['inverter_replacement_year']=st.number_input('Inverter replacement year',min_value=1,max_value=50,value=12)
        params['inverter_replacement_cost_ratio']=st.number_input('Replacement / investment (fraction)',min_value=0.,max_value=1.,value=.1)
        params['tax_credit']=st.number_input('Upfront tax credit / investment (fraction)',min_value=0.,max_value=1.,value=0.)
        params['rebate_amount']=st.number_input('Upfront rebate (€)',min_value=0.,value=0.)
        st.caption('Demand and its interval pattern repeat each year. Generation degrades before self-consumption and exports are recalculated. Incentives are assumed received at year zero.')
    elif mode.startswith('PV'):
        st.write('Upload timestamp, ghi, dni, dhi (interval mean W/m²), temp_air (°C), wind_speed (m/s). Optional measured_generation_kwh must describe this same surface/system and intervals. All timestamps need offsets; interval starts, at most hourly, no gaps.')
        params['latitude']=st.number_input('Latitude',min_value=-90.,max_value=90.,value=52.52)
        params['longitude']=st.number_input('Longitude',min_value=-180.,max_value=180.,value=13.405)
        params['tilt']=st.number_input('Surface tilt from horizontal (degrees)',min_value=0.,max_value=180.,value=90.)
        params['azimuth']=st.number_input('Surface azimuth clockwise from north (degrees)',min_value=0.,max_value=359.99,value=180.)
        params['active_area_m2']=st.number_input('Active PV area (m²)',min_value=.01,value=10.)
        params['efficiency']=st.number_input('DC efficiency at reference conditions (fraction)',min_value=.001,max_value=1.,value=.15)
        params['gamma_pdc']=st.number_input('DC temperature coefficient (1/°C)',min_value=-.02,max_value=0.,value=-.004,format='%.4f')
        params['inverter_efficiency']=st.number_input('Fixed inverter efficiency (fraction)',min_value=.01,max_value=1.,value=.96)
        params['ac_limit_kw']=st.number_input('Inverter AC limit (kW)',min_value=.01,value=1.5)
        params['shading_loss']=st.number_input('User-assumed constant shading loss (fraction)',min_value=0.,max_value=.99,value=0.)
        params['albedo']=st.number_input('Ground albedo',min_value=0.,max_value=1.,value=.2)
        params['thermal_model']=st.selectbox('SAPM mounting assumption',list(pvlib.temperature.TEMPERATURE_MODEL_PARAMETERS['sapm']),index=1)
        st.caption('Isotropic sky transposition, SAPM temperature and linear DC conversion. Fixed shading is an assumption; no geometry-based shading, spectral, soiling or electrical mismatch validation is claimed.')
    else:
        st.write('Upload at least 36 consecutive observed months: date (YYYY-MM-DD), consumption_kwh. The last 12 months are held out; neither model sees these observations during prediction. A separate model is refitted for the next 12 months.')
        params['seed']=st.number_input('Random seed',min_value=0,max_value=2147483647,value=42)
        st.caption('The seasonal-naive baseline repeats the previous year. Holdout error is evidence for that year only; no calibrated uncertainty or multi-decade accuracy is claimed.')
    source=st.text_input('Input provenance (meter, dataset, site and acquisition date)')
    upload=st.file_uploader('Study CSV',type=['csv'],key=f'research_{mode}')
    if upload is None:return
    if upload.size>20_000_000:
        st.error('Limit each study CSV to 20 MB.');return
    try:frame=pd.read_csv(upload)
    except Exception as exc:st.error(f'Could not read CSV: {exc}');return
    fingerprint=input_fingerprint(project_id,mode,params,0,{'source':source,'data':frame})
    if st.button('Evaluate and save study',type='primary'):
        if not source.strip():st.error('Provide input provenance before saving.');return
        try:
            if mode.startswith('Time'):
                rows,summary=matched_balance(frame,params['electricity_price'],params['export_rate'],require_year=True)
                solution={'total_cost':params['cost'],'annual_energy_kwh':summary['generation_kwh'],
                          'annual_demand_kwh':summary['demand_kwh'],'balance_method':BALANCE_VERSION}
                flows,details=create_cash_flow_analysis(solution,params,params['lifetime'],interval_profile=frame)
                irr=calculate_irr(flows)
                result={'summary':summary,'intervals':rows,'cash_flows':pd.DataFrame(details),
                        'finance':{'npv_eur':calculate_npv(flows,params['discount']),
                                   'irr_percent':irr*100 if irr is not None else None,
                                   'payback_years':calculate_payback_period(flows)}}
                version=BALANCE_VERSION
            elif mode.startswith('PV'):
                modeled=pv_profile(frame,**params)
                metrics=None
                if 'measured_generation_kwh' in frame:
                    measured,_=interval_frame(frame,['measured_generation_kwh'])
                    if (measured.measured_generation_kwh<0).any():raise ValueError('Measured generation must be nonnegative')
                    metrics=validation_metrics(modeled.generation_kwh,measured.measured_generation_kwh)
                result={'profile':modeled,'measured_comparison':metrics,'pvlib_version':pvlib.__version__,
                        'validation_scope':'uploaded observations only' if metrics else 'numerical model only; no measured validation'}
                version=PHYSICS_VERSION
            else:
                result=evaluate_forecast(frame,params['seed']);version=FORECAST_VERSION
            conn=db_manager.get_connection()
            if not conn:raise ValueError('No authorized database connection')
            try:
                with conn:
                    run_id=append_run(conn,project_id,'research-study',mode,{'parameters':params,'provenance':source,'data':frame},result,version)
            finally:conn.close()
            st.session_state['_research_result']={'fingerprint':fingerprint,'result':result,'run_id':run_id}
        except Exception as exc:st.error(f'Study not saved: {exc}')
    saved=st.session_state.get('_research_result',{})
    if saved.get('fingerprint')==fingerprint:
        st.success(f'Saved study {saved["run_id"]}')
        for name,value in saved['result'].items():
            st.subheader(name.replace('_',' ').title())
            if isinstance(value,pd.DataFrame):st.dataframe(value,hide_index=True)
            else:st.json(canonical(value))
        st.download_button('Download study results',canonical(saved['result']),file_name=f'study-{saved["run_id"]}.json',mime='application/json')
