import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json

def validate_csv_data(df, required_columns, optional_columns=None):
    """Validate CSV data structure and content."""
    
    validation_results = {
        'is_valid': True,
        'errors': [],
        'warnings': [],
        'summary': {}
    }
    
    # Check required columns
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        validation_results['is_valid'] = False
        validation_results['errors'].append(f"Missing required columns: {missing_columns}")
    
    # Check optional columns
    if optional_columns:
        available_optional = [col for col in optional_columns if col in df.columns]
        validation_results['summary']['optional_columns_found'] = available_optional
    
    # Data quality checks
    if validation_results['is_valid']:
        # Check for empty data
        if len(df) == 0:
            validation_results['is_valid'] = False
            validation_results['errors'].append("Dataset is empty")
        
        # Check for null values in required columns
        for col in required_columns:
            if col in df.columns:
                null_count = df[col].isnull().sum()
                if null_count > 0:
                    validation_results['warnings'].append(f"Column '{col}' has {null_count} null values")
        
        # Data type validation
        if 'Date' in df.columns:
            try:
                pd.to_datetime(df['Date'])
                validation_results['summary']['date_format'] = 'Valid'
            except:
                validation_results['errors'].append("Date column contains invalid date formats")
                validation_results['is_valid'] = False
        
        # Numeric column validation
        numeric_columns = ['Consumption', 'Temperature', 'Humidity', 'Solar_Irradiance']
        for col in numeric_columns:
            if col in df.columns:
                if not pd.api.types.is_numeric_dtype(df[col]):
                    try:
                        pd.to_numeric(df[col], errors='coerce')
                        validation_results['warnings'].append(f"Column '{col}' converted to numeric")
                    except:
                        validation_results['errors'].append(f"Column '{col}' contains non-numeric data")
    
    validation_results['summary']['total_rows'] = len(df)
    validation_results['summary']['total_columns'] = len(df.columns)
    
    return validation_results

def clean_energy_data(df):
    """Clean and preprocess energy consumption data."""
    
    df_clean = df.copy()
    
    # Convert date column
    if 'Date' in df_clean.columns:
        df_clean['Date'] = pd.to_datetime(df_clean['Date'])
        df_clean = df_clean.sort_values('Date')
    
    # Convert numeric columns
    numeric_columns = ['Consumption', 'Temperature', 'Humidity', 'Solar_Irradiance']
    for col in numeric_columns:
        if col in df_clean.columns:
            df_clean[col] = pd.to_numeric(df_clean[col], errors='coerce')
    
    # Remove outliers (values beyond 3 standard deviations)
    if 'Consumption' in df_clean.columns:
        consumption_mean = df_clean['Consumption'].mean()
        consumption_std = df_clean['Consumption'].std()
        outlier_threshold = 3 * consumption_std
        
        outliers = abs(df_clean['Consumption'] - consumption_mean) > outlier_threshold
        if outliers.sum() > 0:
            df_clean.loc[outliers, 'Consumption'] = np.nan
    
    # Fill missing values
    numeric_cols = df_clean.select_dtypes(include=[np.number]).columns
    for col in numeric_cols:
        if col in df_clean.columns:
            # Use forward fill, then backward fill, then mean
            df_clean[col] = df_clean[col].fillna(method='ffill').fillna(method='bfill').fillna(df_clean[col].mean())
    
    # Add derived features
    if 'Date' in df_clean.columns:
        df_clean['Year'] = df_clean['Date'].dt.year
        df_clean['Month'] = df_clean['Date'].dt.month
        df_clean['DayOfYear'] = df_clean['Date'].dt.dayofyear
        df_clean['Quarter'] = df_clean['Date'].dt.quarter
        df_clean['Season'] = df_clean['Month'].map({
            12: 'Winter', 1: 'Winter', 2: 'Winter',
            3: 'Spring', 4: 'Spring', 5: 'Spring',
            6: 'Summer', 7: 'Summer', 8: 'Summer',
            9: 'Fall', 10: 'Fall', 11: 'Fall'
        })
    
    return df_clean

def process_tree_data(df):
    """Process and validate tree shading data."""
    
    required_columns = ['x', 'y', 'height', 'canopy_radius']
    
    # Validate required columns
    validation = validate_csv_data(df, required_columns)
    if not validation['is_valid']:
        raise ValueError(f"Tree data validation failed: {validation['errors']}")
    
    df_processed = df.copy()
    
    # Convert to numeric
    for col in required_columns:
        df_processed[col] = pd.to_numeric(df_processed[col], errors='coerce')
    
    # Remove invalid entries
    df_processed = df_processed.dropna(subset=required_columns)
    
    # Validate reasonable values
    df_processed = df_processed[
        (df_processed['height'] > 0) & (df_processed['height'] < 50) &  # Height 0-50m
        (df_processed['canopy_radius'] > 0) & (df_processed['canopy_radius'] < 25) &  # Radius 0-25m
        (abs(df_processed['x']) < 1000) & (abs(df_processed['y']) < 1000)  # Position within 1km
    ]
    
    # Calculate additional properties
    df_processed['canopy_area'] = np.pi * df_processed['canopy_radius'] ** 2
    df_processed['volume'] = df_processed['canopy_area'] * df_processed['height']
    df_processed['distance_from_origin'] = np.sqrt(df_processed['x']**2 + df_processed['y']**2)
    
    return df_processed

def aggregate_monthly_data(df, value_column, date_column='Date'):
    """Aggregate data to monthly resolution."""
    
    df_monthly = df.copy()
    df_monthly[date_column] = pd.to_datetime(df_monthly[date_column])
    
    # Create monthly grouping
    df_monthly['year_month'] = df_monthly[date_column].dt.to_period('M')
    
    # Aggregate by month
    monthly_agg = df_monthly.groupby('year_month').agg({
        value_column: ['sum', 'mean', 'max', 'min', 'std'],
        date_column: 'first'
    }).round(2)
    
    # Flatten column names
    monthly_agg.columns = [f"{col[1]}_{col[0]}" if col[1] != '' else col[0] for col in monthly_agg.columns]
    
    # Reset index
    monthly_agg = monthly_agg.reset_index()
    
    return monthly_agg

def interpolate_missing_data(df, columns, method='linear'):
    """Interpolate missing data in specified columns."""
    
    df_interpolated = df.copy()
    
    for col in columns:
        if col in df_interpolated.columns:
            if method == 'linear':
                df_interpolated[col] = df_interpolated[col].interpolate(method='linear')
            elif method == 'spline':
                df_interpolated[col] = df_interpolated[col].interpolate(method='spline', order=2)
            elif method == 'seasonal':
                # Use seasonal decomposition for interpolation
                if len(df_interpolated) >= 24:  # Need at least 2 years of monthly data
                    df_interpolated[col] = df_interpolated[col].interpolate(method='time')
                else:
                    df_interpolated[col] = df_interpolated[col].interpolate(method='linear')
    
    return df_interpolated

def detect_anomalies(df, column, method='iqr', threshold=1.5):
    """Detect anomalies in data using various methods."""
    
    anomalies = pd.Series(False, index=df.index)
    
    if method == 'iqr':
        # Interquartile Range method
        Q1 = df[column].quantile(0.25)
        Q3 = df[column].quantile(0.75)
        IQR = Q3 - Q1
        lower_bound = Q1 - threshold * IQR
        upper_bound = Q3 + threshold * IQR
        anomalies = (df[column] < lower_bound) | (df[column] > upper_bound)
    
    elif method == 'zscore':
        # Z-score method
        z_scores = np.abs((df[column] - df[column].mean()) / df[column].std())
        anomalies = z_scores > threshold
    
    elif method == 'rolling':
        # Rolling statistics method
        window = min(30, len(df) // 4)  # 30 days or 1/4 of data
        rolling_mean = df[column].rolling(window=window, center=True).mean()
        rolling_std = df[column].rolling(window=window, center=True).std()
        
        lower_bound = rolling_mean - threshold * rolling_std
        upper_bound = rolling_mean + threshold * rolling_std
        anomalies = (df[column] < lower_bound) | (df[column] > upper_bound)
    
    return anomalies

def normalize_data(df, columns, method='minmax'):
    """Normalize data columns using specified method."""
    
    df_normalized = df.copy()
    
    for col in columns:
        if col in df_normalized.columns:
            if method == 'minmax':
                # Min-Max normalization (0-1)
                min_val = df_normalized[col].min()
                max_val = df_normalized[col].max()
                df_normalized[f"{col}_normalized"] = (df_normalized[col] - min_val) / (max_val - min_val)
            
            elif method == 'zscore':
                # Z-score normalization (mean=0, std=1)
                mean_val = df_normalized[col].mean()
                std_val = df_normalized[col].std()
                df_normalized[f"{col}_normalized"] = (df_normalized[col] - mean_val) / std_val
            
            elif method == 'robust':
                # Robust normalization using median and IQR
                median_val = df_normalized[col].median()
                iqr_val = df_normalized[col].quantile(0.75) - df_normalized[col].quantile(0.25)
                df_normalized[f"{col}_normalized"] = (df_normalized[col] - median_val) / iqr_val
    
    return df_normalized

def export_processed_data(data_dict, format_type='csv'):
    """Export processed data in various formats."""
    
    exported_files = {}
    
    if format_type == 'csv':
        for name, df in data_dict.items():
            if isinstance(df, pd.DataFrame):
                exported_files[f"{name}.csv"] = df.to_csv(index=False)
    
    elif format_type == 'json':
        for name, data in data_dict.items():
            if isinstance(data, pd.DataFrame):
                exported_files[f"{name}.json"] = data.to_json(orient='records', indent=2)
            else:
                exported_files[f"{name}.json"] = json.dumps(data, indent=2, default=str)
    
    elif format_type == 'excel':
        # Would require openpyxl in production
        for name, df in data_dict.items():
            if isinstance(df, pd.DataFrame):
                exported_files[f"{name}.xlsx"] = f"Excel export for {name} (requires openpyxl)"
    
    return exported_files

def create_data_summary(df, title="Data Summary"):
    """Create comprehensive data summary statistics."""
    
    summary = {
        'title': title,
        'basic_info': {
            'total_rows': len(df),
            'total_columns': len(df.columns),
            'memory_usage': f"{df.memory_usage(deep=True).sum() / 1024**2:.2f} MB",
            'date_range': None
        },
        'column_info': {},
        'data_quality': {
            'missing_values': df.isnull().sum().to_dict(),
            'duplicate_rows': df.duplicated().sum(),
            'data_types': df.dtypes.astype(str).to_dict()
        },
        'numeric_summary': {},
        'categorical_summary': {}
    }
    
    # Date range if date column exists
    date_columns = df.select_dtypes(include=['datetime64']).columns
    if len(date_columns) > 0:
        date_col = date_columns[0]
        summary['basic_info']['date_range'] = {
            'start': df[date_col].min().strftime('%Y-%m-%d'),
            'end': df[date_col].max().strftime('%Y-%m-%d'),
            'duration_days': (df[date_col].max() - df[date_col].min()).days
        }
    
    # Numeric columns summary
    numeric_columns = df.select_dtypes(include=[np.number]).columns
    if len(numeric_columns) > 0:
        summary['numeric_summary'] = df[numeric_columns].describe().round(2).to_dict()
    
    # Categorical columns summary
    categorical_columns = df.select_dtypes(include=['object']).columns
    for col in categorical_columns:
        summary['categorical_summary'][col] = {
            'unique_values': df[col].nunique(),
            'top_values': df[col].value_counts().head().to_dict(),
            'null_count': df[col].isnull().sum()
        }
    
    return summary
