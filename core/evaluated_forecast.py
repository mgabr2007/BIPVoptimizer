"""Fixed-origin 12-month holdout evaluation, then a separate 12-month forecast.

No future/held-out observations enter training or recursive holdout features.
No calibrated uncertainty intervals or multi-decade forecast accuracy are claimed.
"""
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from core.energy_contracts import reference_year
from core.time_series_research import validation_metrics

VERSION='monthly-rf-holdout-v1'


def features(history,month):
    return [history[-1],history[-12],float(np.mean(history[-3:])),
            np.sin(2*np.pi*month/12),np.cos(2*np.pi*month/12)]


def fit(values,dates,seed):
    x=[features(values[:i],dates[i].month) for i in range(12,len(values))]
    model=RandomForestRegressor(n_estimators=100,min_samples_leaf=2,random_state=seed,n_jobs=1)
    return model.fit(x,values[12:])


def recursive(model,history,dates):
    past=list(history);result=[]
    for date in dates:
        prediction=max(0.,float(model.predict([features(past,date.month)])[0]))
        past.append(prediction);result.append(prediction)
    return result


def evaluate_forecast(frame,seed=42):
    if not {'date','consumption_kwh'}.issubset(frame.columns):raise ValueError('CSV requires date, consumption_kwh')
    dates=pd.DatetimeIndex(pd.to_datetime(frame.date,errors='raise'))
    values=frame.consumption_kwh.to_numpy(dtype=float)
    reference_year(values,[d.strftime('%Y-%m-%d') for d in dates])
    if len(values)<36:raise ValueError('At least 36 consecutive observed months are required')
    train=values[:-12];test=values[-12:];test_dates=dates[-12:]
    model=fit(train,dates[:-12],seed)
    prediction=recursive(model,train,test_dates)
    baseline=train[-12:]
    metrics=pd.DataFrame([{'method':'Random forest',**validation_metrics(prediction,test)},
                          {'method':'Seasonal naive',**validation_metrics(baseline,test)}])
    future_dates=pd.date_range(dates[-1].to_period('M').to_timestamp()+pd.offsets.MonthBegin(1),periods=12,freq='MS')
    future=recursive(fit(values,dates,seed),values,future_dates)
    return {'evaluation':pd.DataFrame({'date':test_dates,'observed_kwh':test,
                                      'random_forest_kwh':prediction,'seasonal_naive_kwh':baseline}),
            'metrics':metrics,'forecast':pd.DataFrame({'date':future_dates,'forecast_kwh':future}),
            'metadata':{'version':VERSION,'seed':seed,'training_months':len(train),'holdout_months':12,
                        'train_end':str(dates[-13]),'holdout_start':str(test_dates[0]),'holdout_end':str(test_dates[-1]),
                        'protocol':'fixed-origin recursive 12-month holdout; refit all data only for future forecast',
                        'uncertainty':'not calibrated','accuracy_scope':'one observed holdout year only'}}
