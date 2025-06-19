import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import os
from typing import Dict, List, Optional, Tuple

class WeatherDataAPI:
    """
    Weather data API handler for OpenWeatherMap and other weather services.
    """
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv('OPENWEATHER_API_KEY')
        self.base_url = "http://api.openweathermap.org/data/2.5"
        self.onecall_url = "http://api.openweathermap.org/data/3.0/onecall"
        self.session = requests.Session()
        
    def get_current_weather(self, lat: float, lon: float) -> Dict:
        """
        Get current weather conditions.
        
        Args:
            lat (float): Latitude
            lon (float): Longitude
            
        Returns:
            dict: Current weather data
        """
        
        if not self.api_key:
            raise ValueError("API key is required for weather data access")
        
        url = f"{self.base_url}/weather"
        params = {
            'lat': lat,
            'lon': lon,
            'appid': self.api_key,
            'units': 'metric'
        }
        
        try:
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            # Parse and structure the response
            weather_data = {
                'location': {
                    'name': data.get('name', 'Unknown'),
                    'country': data.get('sys', {}).get('country', 'Unknown'),
                    'latitude': lat,
                    'longitude': lon
                },
                'current': {
                    'temperature': data['main']['temp'],
                    'feels_like': data['main']['feels_like'],
                    'humidity': data['main']['humidity'],
                    'pressure': data['main']['pressure'],
                    'wind_speed': data.get('wind', {}).get('speed', 0),
                    'wind_direction': data.get('wind', {}).get('deg', 0),
                    'cloudiness': data['clouds']['all'],
                    'visibility': data.get('visibility', 10000) / 1000,  # Convert to km
                    'description': data['weather'][0]['description'],
                    'timestamp': datetime.fromtimestamp(data['dt'])
                }
            }
            
            return weather_data
            
        except requests.RequestException as e:
            raise Exception(f"Failed to fetch current weather data: {str(e)}")
        except KeyError as e:
            raise Exception(f"Unexpected weather data format: {str(e)}")
    
    def get_historical_weather(self, lat: float, lon: float, start_date: datetime, 
                             end_date: datetime = None) -> List[Dict]:
        """
        Get historical weather data.
        
        Args:
            lat (float): Latitude
            lon (float): Longitude
            start_date (datetime): Start date for historical data
            end_date (datetime): End date (optional, defaults to start_date + 1 day)
            
        Returns:
            list: Historical weather data
        """
        
        if not self.api_key:
            raise ValueError("API key is required for weather data access")
        
        if end_date is None:
            end_date = start_date + timedelta(days=1)
        
        historical_data = []
        current_date = start_date
        
        while current_date <= end_date:
            timestamp = int(current_date.timestamp())
            
            url = f"{self.onecall_url}/timemachine"
            params = {
                'lat': lat,
                'lon': lon,
                'dt': timestamp,
                'appid': self.api_key,
                'units': 'metric'
            }
            
            try:
                response = self.session.get(url, params=params, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Extract hourly data
                    for hour_data in data.get('data', []):
                        parsed_data = {
                            'datetime': datetime.fromtimestamp(hour_data['dt']),
                            'temperature': hour_data['temp'],
                            'humidity': hour_data['humidity'],
                            'pressure': hour_data['pressure'],
                            'wind_speed': hour_data.get('wind_speed', 0),
                            'wind_direction': hour_data.get('wind_deg', 0),
                            'cloudiness': hour_data.get('clouds', 0),
                            'description': hour_data.get('weather', [{}])[0].get('description', 'Unknown')
                        }
                        historical_data.append(parsed_data)
                
                current_date += timedelta(days=1)
                
            except requests.RequestException as e:
                print(f"Warning: Failed to fetch data for {current_date}: {str(e)}")
                current_date += timedelta(days=1)
                continue
        
        return historical_data
    
    def generate_tmy_data(self, lat: float, lon: float, year: int = None) -> pd.DataFrame:
        """
        Generate Typical Meteorological Year (TMY) data.
        
        Args:
            lat (float): Latitude
            lon (float): Longitude
            year (int): Year for TMY data (defaults to current year)
            
        Returns:
            pd.DataFrame: TMY data with hourly resolution
        """
        
        if year is None:
            year = datetime.now().year
        
        # Generate hourly timestamps for the year
        start_date = datetime(year, 1, 1)
        end_date = datetime(year, 12, 31, 23)
        dates = pd.date_range(start_date, end_date, freq='H')
        
        # Calculate solar radiation components
        tmy_data = []
        
        for dt in dates:
            day_of_year = dt.timetuple().tm_yday
            hour = dt.hour
            
            # Solar geometry calculations
            declination = 23.45 * np.sin(np.radians(360 * (284 + day_of_year) / 365))
            hour_angle = 15 * (hour - 12)
            
            # Solar elevation angle
            lat_rad = np.radians(lat)
            dec_rad = np.radians(declination)
            hour_rad = np.radians(hour_angle)
            
            elevation = np.arcsin(
                np.sin(lat_rad) * np.sin(dec_rad) + 
                np.cos(lat_rad) * np.cos(dec_rad) * np.cos(hour_rad)
            )
            
            elevation_deg = np.degrees(elevation)
            
            # Calculate solar irradiance components
            if elevation_deg > 0:
                # Extraterrestrial radiation
                solar_constant = 1367  # W/m²
                eccentricity = 1 + 0.033 * np.cos(np.radians(360 * day_of_year / 365))
                extraterrestrial = solar_constant * eccentricity * np.sin(elevation)
                
                # Atmospheric attenuation (simplified model)
                air_mass = 1 / (np.sin(elevation) + 0.50572 * (elevation_deg + 6.07995)**(-1.6364))
                air_mass = max(1, min(40, air_mass))
                
                # Clear sky model
                tau_beam = 0.9 * np.exp(-0.15 * air_mass)  # Beam transmittance
                tau_diffuse = 0.3  # Diffuse transmittance
                
                # Weather variability factor
                np.random.seed(day_of_year * 24 + hour)  # Reproducible randomness
                weather_factor = 0.7 + 0.6 * np.random.random()
                
                # Calculate irradiance components
                dni = max(0, extraterrestrial * tau_beam * weather_factor)
                dhi = max(0, extraterrestrial * tau_diffuse * weather_factor)
                ghi = max(0, dni * np.sin(elevation) + dhi)
            else:
                ghi = dni = dhi = 0
            
            # Generate weather parameters
            # Temperature model (sinusoidal with daily and seasonal variation)
            temp_base = 15 + 10 * np.sin(2 * np.pi * (day_of_year - 80) / 365)  # Seasonal
            temp_daily = 5 * np.sin(2 * np.pi * (hour - 6) / 24)  # Daily variation
            temperature = temp_base + temp_daily + 2 * (np.random.random() - 0.5)
            
            # Humidity (inverse correlation with temperature)
            humidity = max(20, min(95, 80 - (temperature - 15) + 10 * (np.random.random() - 0.5)))
            
            # Wind speed
            wind_speed = max(0, 3 + 2 * np.random.normal())
            
            # Pressure (with elevation correction)
            elevation_m = 100  # Assume 100m elevation
            pressure = 1013.25 * (1 - 0.0065 * elevation_m / 288.15)**(9.80665 * 0.0289644 / (8.31447 * 0.0065))
            
            tmy_data.append({
                'datetime': dt,
                'GHI': ghi,
                'DNI': dni,
                'DHI': dhi,
                'temperature': temperature,
                'humidity': humidity,
                'pressure': pressure,
                'wind_speed': wind_speed,
                'wind_direction': (day_of_year * 3 + hour * 15) % 360
            })
        
        # Convert to DataFrame
        tmy_df = pd.DataFrame(tmy_data)
        
        # Apply realistic constraints
        tmy_df['GHI'] = np.clip(tmy_df['GHI'], 0, 1200)
        tmy_df['DNI'] = np.clip(tmy_df['DNI'], 0, 1000)
        tmy_df['DHI'] = np.clip(tmy_df['DHI'], 0, 500)
        tmy_df['temperature'] = np.clip(tmy_df['temperature'], -30, 50)
        tmy_df['humidity'] = np.clip(tmy_df['humidity'], 10, 100)
        tmy_df['wind_speed'] = np.clip(tmy_df['wind_speed'], 0, 20)
        
        return tmy_df
    
    def validate_weather_data(self, data: pd.DataFrame) -> Dict:
        """
        Validate weather data quality and completeness.
        
        Args:
            data (pd.DataFrame): Weather data to validate
            
        Returns:
            dict: Validation results
        """
        
        validation = {
            'is_valid': True,
            'errors': [],
            'warnings': [],
            'statistics': {}
        }
        
        required_columns = ['datetime', 'GHI', 'temperature']
        optional_columns = ['DNI', 'DHI', 'humidity', 'wind_speed', 'pressure']
        
        # Check required columns
        missing_required = [col for col in required_columns if col not in data.columns]
        if missing_required:
            validation['is_valid'] = False
            validation['errors'].append(f"Missing required columns: {missing_required}")
        
        # Check data completeness
        if len(data) == 0:
            validation['is_valid'] = False
            validation['errors'].append("No data provided")
            return validation
        
        # Check for null values
        for col in required_columns:
            if col in data.columns:
                null_count = data[col].isnull().sum()
                if null_count > 0:
                    null_percentage = (null_count / len(data)) * 100
                    if null_percentage > 10:
                        validation['errors'].append(f"Column '{col}' has {null_percentage:.1f}% null values")
                    else:
                        validation['warnings'].append(f"Column '{col}' has {null_count} null values")
        
        # Check data ranges
        if 'GHI' in data.columns:
            ghi_data = data['GHI'].dropna()
            if len(ghi_data) > 0:
                if ghi_data.max() > 1500:
                    validation['warnings'].append("GHI values exceed typical maximum (1500 W/m²)")
                if ghi_data.min() < 0:
                    validation['warnings'].append("Negative GHI values found")
                validation['statistics']['GHI'] = {
                    'min': ghi_data.min(),
                    'max': ghi_data.max(),
                    'mean': ghi_data.mean(),
                    'std': ghi_data.std()
                }
        
        if 'temperature' in data.columns:
            temp_data = data['temperature'].dropna()
            if len(temp_data) > 0:
                if temp_data.max() > 60:
                    validation['warnings'].append("Temperature values exceed typical maximum (60°C)")
                if temp_data.min() < -50:
                    validation['warnings'].append("Temperature values below typical minimum (-50°C)")
                validation['statistics']['temperature'] = {
                    'min': temp_data.min(),
                    'max': temp_data.max(),
                    'mean': temp_data.mean(),
                    'std': temp_data.std()
                }
        
        # Check time series continuity
        if 'datetime' in data.columns:
            try:
                datetime_data = pd.to_datetime(data['datetime'])
                time_diff = datetime_data.diff().dropna()
                
                if len(time_diff) > 0:
                    most_common_interval = time_diff.mode()[0]
                    validation['statistics']['time_interval'] = str(most_common_interval)
                    
                    # Check for gaps
                    large_gaps = time_diff[time_diff > most_common_interval * 2]
                    if len(large_gaps) > 0:
                        validation['warnings'].append(f"Found {len(large_gaps)} time gaps in data")
                
            except Exception as e:
                validation['errors'].append(f"Invalid datetime format: {str(e)}")
        
        return validation
    
    def calculate_solar_radiation_statistics(self, data: pd.DataFrame) -> Dict:
        """
        Calculate solar radiation statistics from weather data.
        
        Args:
            data (pd.DataFrame): Weather data with radiation components
            
        Returns:
            dict: Solar radiation statistics
        """
        
        stats = {}
        
        # Basic radiation statistics
        for component in ['GHI', 'DNI', 'DHI']:
            if component in data.columns:
                radiation_data = data[component].dropna()
                
                if len(radiation_data) > 0:
                    stats[component] = {
                        'annual_sum': radiation_data.sum(),
                        'annual_mean': radiation_data.mean(),
                        'peak_value': radiation_data.max(),
                        'total_hours_above_100': (radiation_data > 100).sum(),
                        'total_hours_above_500': (radiation_data > 500).sum(),
                        'total_hours_above_800': (radiation_data > 800).sum(),
                        'percentile_95': radiation_data.quantile(0.95),
                        'percentile_5': radiation_data.quantile(0.05)
                    }
        
        # Monthly statistics
        if 'datetime' in data.columns and 'GHI' in data.columns:
            data_copy = data.copy()
            data_copy['datetime'] = pd.to_datetime(data_copy['datetime'])
            data_copy['month'] = data_copy['datetime'].dt.month
            
            monthly_stats = data_copy.groupby('month')['GHI'].agg([
                'sum', 'mean', 'max', 'std'
            ]).round(2)
            
            stats['monthly_ghi'] = monthly_stats.to_dict()
        
        # Clearness index (if DNI and GHI available)
        if 'GHI' in data.columns and 'DNI' in data.columns:
            ghi_data = data['GHI']
            dni_data = data['DNI']
            
            # Calculate clearness index
            extraterrestrial = 1367  # Solar constant
            clearness_index = ghi_data / extraterrestrial
            clearness_index = clearness_index.clip(0, 1)
            
            stats['clearness_index'] = {
                'mean': clearness_index.mean(),
                'std': clearness_index.std(),
                'clear_days_fraction': (clearness_index > 0.7).mean(),
                'cloudy_days_fraction': (clearness_index < 0.3).mean()
            }
        
        return stats
    
    def export_weather_data(self, data: pd.DataFrame, filename: str, format_type: str = 'csv') -> str:
        """
        Export weather data to file.
        
        Args:
            data (pd.DataFrame): Weather data to export
            filename (str): Output filename
            format_type (str): Export format ('csv', 'json', 'excel')
            
        Returns:
            str: Export status message
        """
        
        try:
            if format_type.lower() == 'csv':
                data.to_csv(filename, index=False)
                return f"Weather data exported to {filename} (CSV format)"
            
            elif format_type.lower() == 'json':
                data_dict = data.to_dict(orient='records')
                with open(filename, 'w') as f:
                    json.dump(data_dict, f, indent=2, default=str)
                return f"Weather data exported to {filename} (JSON format)"
            
            elif format_type.lower() == 'excel':
                data.to_excel(filename, index=False)
                return f"Weather data exported to {filename} (Excel format)"
            
            else:
                raise ValueError(f"Unsupported export format: {format_type}")
                
        except Exception as e:
            return f"Export failed: {str(e)}"

def create_weather_summary(weather_data: pd.DataFrame) -> Dict:
    """
    Create comprehensive weather data summary.
    
    Args:
        weather_data (pd.DataFrame): Weather data
        
    Returns:
        dict: Weather summary statistics
    """
    
    summary = {
        'data_period': {},
        'temperature': {},
        'solar_radiation': {},
        'wind': {},
        'humidity': {}
    }
    
    # Data period
    if 'datetime' in weather_data.columns:
        dates = pd.to_datetime(weather_data['datetime'])
        summary['data_period'] = {
            'start_date': dates.min().strftime('%Y-%m-%d'),
            'end_date': dates.max().strftime('%Y-%m-%d'),
            'total_hours': len(weather_data),
            'total_days': (dates.max() - dates.min()).days + 1
        }
    
    # Temperature statistics
    if 'temperature' in weather_data.columns:
        temp_data = weather_data['temperature'].dropna()
        summary['temperature'] = {
            'mean': temp_data.mean(),
            'min': temp_data.min(),
            'max': temp_data.max(),
            'std': temp_data.std(),
            'heating_degree_days': max(0, (18 - temp_data).clip(lower=0).sum()),
            'cooling_degree_days': max(0, (temp_data - 18).clip(lower=0).sum())
        }
    
    # Solar radiation statistics
    if 'GHI' in weather_data.columns:
        ghi_data = weather_data['GHI'].dropna()
        summary['solar_radiation'] = {
            'annual_irradiation': ghi_data.sum(),
            'peak_irradiance': ghi_data.max(),
            'mean_irradiance': ghi_data.mean(),
            'sunshine_hours': (ghi_data > 120).sum(),  # Hours with significant sun
            'peak_sun_hours': ghi_data.sum() / 1000  # Equivalent peak sun hours
        }
    
    # Wind statistics
    if 'wind_speed' in weather_data.columns:
        wind_data = weather_data['wind_speed'].dropna()
        summary['wind'] = {
            'mean_speed': wind_data.mean(),
            'max_speed': wind_data.max(),
            'std_speed': wind_data.std(),
            'calm_hours': (wind_data < 1).sum(),  # Hours with very low wind
            'strong_wind_hours': (wind_data > 10).sum()  # Hours with strong wind
        }
    
    # Humidity statistics
    if 'humidity' in weather_data.columns:
        humidity_data = weather_data['humidity'].dropna()
        summary['humidity'] = {
            'mean': humidity_data.mean(),
            'min': humidity_data.min(),
            'max': humidity_data.max(),
            'std': humidity_data.std(),
            'high_humidity_hours': (humidity_data > 80).sum(),
            'low_humidity_hours': (humidity_data < 30).sum()
        }
    
    return summary
