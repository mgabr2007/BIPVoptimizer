"""Explicit interval contracts and a bounded PV model, separate from annual estimates."""
import numpy as np
import pandas as pd
import pvlib
from core.energy_contracts import nonnegative

BALANCE_VERSION = 'time-matched-no-storage-v1'
PHYSICS_VERSION = 'pvlib-isotropic-sapm-linear-dc-v1'


def interval_frame(frame, columns, require_year=False):
    """Timestamps are interval starts with explicit UTC offsets; values are interval totals.

    No filling, resampling, sorting, deduplication or timezone guessing is performed.
    """
    if not {'timestamp', *columns}.issubset(frame.columns):
        raise ValueError(f'Required columns: timestamp, {", ".join(columns)}')
    stamps = [pd.Timestamp(x) for x in frame['timestamp']]
    if any(pd.isna(t) or t.tzinfo is None for t in stamps):
        raise ValueError('Every timestamp must include a timezone offset or Z')
    index = pd.DatetimeIndex(pd.to_datetime(stamps, utc=True))
    if len(index) < 2 or not index.is_monotonic_increasing or index.has_duplicates:
        raise ValueError('At least two unique, ordered timestamps are required')
    delta = np.diff(index.asi8)
    if not np.all(delta == delta[0]) or delta[0] <= 0 or delta[0] > 3600e9:
        raise ValueError('Intervals must be regular, gap-free and at most one hour')
    data = frame[list(columns)].apply(pd.to_numeric, errors='raise').to_numpy(dtype=float)
    if not np.isfinite(data).all():
        raise ValueError('Values must be finite; missing intervals cannot be filled silently')
    duration = pd.Timedelta(int(delta[0]), unit='ns')
    if require_year:
        start = index[0]
        if (start.month, start.day, start.hour, start.minute, start.second) != (1, 1, 0, 0, 0) or index[-1]+duration != start+pd.DateOffset(years=1):
            raise ValueError('Annual research requires one complete UTC calendar year, including leap day')
    return pd.DataFrame(data, index=index, columns=columns), duration.total_seconds()/3600


def matched_balance(frame, import_rate, export_rate, require_year=False):
    data, hours = interval_frame(frame, ['generation_kwh','demand_kwh'], require_year)
    if (data.to_numpy() < 0).any():
        raise ValueError('Generation and demand must be nonnegative interval kWh')
    data['offset_kwh'] = np.minimum(data.generation_kwh, data.demand_kwh)
    data['surplus_kwh'] = data.generation_kwh-data.offset_kwh
    data['net_import_kwh'] = data.demand_kwh-data.offset_kwh
    data['avoided_import_cost'] = data.offset_kwh*nonnegative(import_rate, 'Import tariff')
    data['export_revenue'] = data.surplus_kwh*nonnegative(export_rate, 'Export tariff')
    summary = {key:float(value) for key,value in data.sum().items()}
    summary.update(gross_benefit=summary['avoided_import_cost']+summary['export_revenue'],
                   balance_method=BALANCE_VERSION, interval_hours=hours,
                   storage=False, curtailment=False)
    return data.reset_index(names='timestamp'), summary


def pv_profile(weather, *, latitude, longitude, tilt, azimuth, active_area_m2,
               efficiency, gamma_pdc=-.004, inverter_efficiency=.96, ac_limit_kw=1e9,
               shading_loss=0., albedo=.2, thermal_model='close_mount_glass_glass'):
    """Isotropic POA + specified SAPM temperature + linear DC + fixed-efficiency clipping.

    Weather is interval-mean irradiance W/m², air °C and wind m/s. Solar position
    is evaluated at interval midpoints. Shading is a user loss fraction, not ray tracing.
    No spectral/mismatch/soiling model or field-validation claim is made.
    """
    columns=['ghi','dni','dhi','temp_air','wind_speed']
    data,hours=interval_frame(weather,columns)
    values=[latitude,longitude,tilt,azimuth,active_area_m2,efficiency,gamma_pdc,
            inverter_efficiency,ac_limit_kw,shading_loss,albedo]
    if not np.isfinite(values).all():raise ValueError('PV parameters must be finite')
    if not (-90<=latitude<=90 and -180<=longitude<=180 and 0<=tilt<=180 and 0<=azimuth<360):
        raise ValueError('Invalid location or surface orientation')
    if not (active_area_m2>0 and 0<efficiency<=1 and -.02<=gamma_pdc<=0 and
            0<inverter_efficiency<=1 and ac_limit_kw>0 and 0<=shading_loss<1 and 0<=albedo<=1):
        raise ValueError('Invalid area, efficiency, thermal coefficient, clipping or loss setting')
    if (data[['ghi','dni','dhi','wind_speed']]<0).any().any():raise ValueError('Irradiance and wind must be nonnegative')
    thermal=pvlib.temperature.TEMPERATURE_MODEL_PARAMETERS['sapm']
    if thermal_model not in thermal:raise ValueError('Choose an explicit supported SAPM mounting model')
    position=pvlib.solarposition.get_solarposition(data.index+pd.Timedelta(hours=hours/2),latitude,longitude)
    position.index=data.index
    poa=pvlib.irradiance.get_total_irradiance(tilt,azimuth,position.apparent_zenith,position.azimuth,
                                           data.dni,data.ghi,data.dhi,albedo=albedo,model='isotropic')['poa_global']
    poa=poa.clip(lower=0).where(position.apparent_zenith<90,0.)
    cell=pvlib.temperature.sapm_cell(poa,data.temp_air,data.wind_speed,**thermal[thermal_model])
    dc_kw=(poa*active_area_m2*efficiency/1000*(1+gamma_pdc*(cell-25)).clip(lower=0)*(1-shading_loss))
    ac_kw=(dc_kw*inverter_efficiency).clip(upper=ac_limit_kw)
    return pd.DataFrame({'timestamp':data.index,'poa_w_m2':poa.to_numpy(),'cell_temperature_c':cell.to_numpy(),
                         'dc_kw':dc_kw.to_numpy(),'ac_kw':ac_kw.to_numpy(),
                         'generation_kwh':ac_kw.to_numpy()*hours})


def validation_metrics(predicted, measured):
    predicted=np.asarray(predicted,dtype=float);measured=np.asarray(measured,dtype=float)
    if predicted.shape!=measured.shape or predicted.ndim!=1 or len(predicted)<2:
        raise ValueError('At least two aligned measured and predicted values required')
    if not np.isfinite(predicted).all() or not np.isfinite(measured).all():raise ValueError('Finite values required')
    error=predicted-measured
    return {'n':len(error),'mae_kwh':float(np.mean(abs(error))),
            'rmse_kwh':float(np.sqrt(np.mean(error**2))), 'bias_kwh':float(np.mean(error)),
            'normalized_rmse':float(np.sqrt(np.mean(error**2))/np.mean(measured)) if np.mean(measured)>0 else None}
