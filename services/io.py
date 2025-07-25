"""
External I/O services for BIPV Optimizer
Handles database operations, OpenWeather API, and WMO file parsing
"""
import requests
import json
import os
import streamlit as st
from database_manager import db_manager


def get_current_project_id():
    """Get current project ID from session state or database"""
    
    try:
        # First, check if project_id is directly set in project_data (from project switching)
        if 'project_data' in st.session_state and st.session_state.project_data.get('project_id'):
            return st.session_state.project_data['project_id']
        
        # Second, check if project_id is directly in session state
        if 'project_id' in st.session_state:
            return st.session_state.project_id
        
        # Third, try to get from project_name in session state
        project_name = st.session_state.get('project_name')
        if project_name:
            try:
                conn = db_manager.get_connection()
                if conn:
                    with conn.cursor() as cursor:
                        cursor.execute("SELECT id FROM projects WHERE project_name = %s", (project_name,))
                        result = cursor.fetchone()
                        if result:
                            return result[0]
                    conn.close()
            except Exception as e:
                # Don't show error to user here, just continue to next method
                pass
        
        # Fourth, try to get from project_name in project_data
        if 'project_data' in st.session_state and st.session_state.project_data.get('project_name'):
            project_name = st.session_state.project_data['project_name']
            try:
                conn = db_manager.get_connection()
                if conn:
                    with conn.cursor() as cursor:
                        cursor.execute("SELECT id FROM projects WHERE project_name = %s", (project_name,))
                        result = cursor.fetchone()
                        if result:
                            return result[0]
                    conn.close()
            except Exception as e:
                # Don't show error to user here, just continue to next method
                pass
    
    except Exception as e:
        # Catch any KeyError or other issues with session state access
        pass
    
    # Simple fallback: use any available project with data
    try:
        conn = db_manager.get_connection()
        if conn:
            with conn.cursor() as cursor:
                # First try to find project with building elements (most common)
                cursor.execute("""
                    SELECT DISTINCT project_id FROM building_elements 
                    ORDER BY project_id DESC LIMIT 1
                """)
                result = cursor.fetchone()
                if result:
                    fallback_project_id = result[0]
                    st.session_state.current_project_id = fallback_project_id
                    return fallback_project_id
                
                # If no building elements, find any project
                cursor.execute("SELECT id FROM projects ORDER BY id DESC LIMIT 1")
                result = cursor.fetchone()
                if result:
                    return result[0]
            conn.close()
    except Exception as e:
        pass
    
    return None


def load_project_data_from_database(project_id):
    """Load complete project data from database and populate session state"""
    if not project_id:
        return False
    
    try:
        # Get project basic data
        project_data = db_manager.get_project_by_id(project_id)
        if not project_data:
            return False
        
        # Initialize session state project_data if not exists
        if 'project_data' not in st.session_state:
            st.session_state.project_data = {}
        
        # Update session state with database data
        st.session_state.project_data.update({
            'project_id': project_id,
            'project_name': project_data.get('project_name'),
            'location': project_data.get('location'),
            'coordinates': {
                'lat': project_data.get('latitude'),
                'lon': project_data.get('longitude')
            } if project_data.get('latitude') and project_data.get('longitude') else {},
            'timezone': project_data.get('timezone'),
            'currency': project_data.get('currency', 'EUR'),
            'setup_complete': True
        })
        
        # Load electricity rates if available
        if project_data.get('electricity_rates'):
            import json
            try:
                rates = json.loads(project_data['electricity_rates']) if isinstance(project_data['electricity_rates'], str) else project_data['electricity_rates']
                st.session_state.project_data['electricity_rates'] = rates
            except:
                pass
        
        # Set project name in session state for compatibility
        st.session_state.project_name = project_data.get('project_name')
        st.session_state.project_id = project_id
        
        return True
        
    except Exception as e:
        st.error(f"Error loading project data: {str(e)}")
        return False


def ensure_project_data_loaded():
    """Ensure project data is loaded from database when project is selected"""
    project_id = get_current_project_id()
    if project_id:
        # Check if we need to reload data from database
        current_project_id = st.session_state.get('project_data', {}).get('project_id')
        if current_project_id != project_id:
            # Project changed, reload from database
            load_project_data_from_database(project_id)
        return True
    return False


@st.cache_data(ttl=3600)
def load_complete_wmo_stations():
    """Load all WMO stations from the official database file"""
    try:
        # Try multiple encodings to handle different file formats
        encodings = ['utf-8', 'latin-1', 'iso-8859-1', 'cp1252']
        content = None
        
        for encoding in encodings:
            try:
                with open('attached_assets/stations_list_CLIMAT_data_1750488038242.txt', 'r', encoding=encoding) as f:
                    content = f.read()
                break
            except UnicodeDecodeError:
                continue
        
        if content is None:
            raise UnicodeDecodeError("Unable to decode file with any encoding")
        
        stations = []
        lines = content.strip().split('\n')
        
        for line in lines[1:]:  # Skip header
            parts = line.split('\t')
            if len(parts) >= 4:
                try:
                    station = {
                        'id': parts[0].strip(),
                        'name': parts[1].strip(),
                        'country': parts[2].strip(),
                        'latitude': float(parts[3]) if parts[3].strip() else 0,
                        'longitude': float(parts[4]) if len(parts) > 4 and parts[4].strip() else 0
                    }
                    stations.append(station)
                except (ValueError, IndexError):
                    continue
        
        return stations
    except (FileNotFoundError, UnicodeDecodeError, Exception) as e:
        st.warning(f"Could not load WMO stations file: {str(e)}. Using fallback stations.")
        # Fallback WMO stations for major global cities
        return [
            {'id': '10382', 'name': 'Berlin-Tempelhof', 'country': 'Germany', 'latitude': 52.47, 'longitude': 13.40},
            {'id': '03772', 'name': 'London-Heathrow', 'country': 'United Kingdom', 'latitude': 51.48, 'longitude': -0.45},
            {'id': '08221', 'name': 'Madrid-Barajas', 'country': 'Spain', 'latitude': 40.47, 'longitude': -3.56},
            {'id': '07156', 'name': 'Paris-Le Bourget', 'country': 'France', 'latitude': 48.97, 'longitude': 2.44},
            {'id': '16242', 'name': 'Roma-Fiumicino', 'country': 'Italy', 'latitude': 41.80, 'longitude': 12.25},
            {'id': '06240', 'name': 'Amsterdam-Schiphol', 'country': 'Netherlands', 'latitude': 52.30, 'longitude': 4.76},
            {'id': '11035', 'name': 'Wien-Schwechat', 'country': 'Austria', 'latitude': 48.11, 'longitude': 16.57},
            {'id': '02464', 'name': 'Stockholm-Arlanda', 'country': 'Sweden', 'latitude': 59.65, 'longitude': 17.95},
            {'id': '72278', 'name': 'Phoenix Sky Harbor', 'country': 'United States', 'latitude': 33.43, 'longitude': -112.02},
            {'id': '72565', 'name': 'Denver International', 'country': 'United States', 'latitude': 39.86, 'longitude': -104.66},
            {'id': '72202', 'name': 'Miami International', 'country': 'United States', 'latitude': 25.79, 'longitude': -80.32},
            {'id': '72793', 'name': 'Seattle-Tacoma', 'country': 'United States', 'latitude': 47.45, 'longitude': -122.31},
            {'id': '71508', 'name': 'Toronto Pearson', 'country': 'Canada', 'latitude': 43.68, 'longitude': -79.63},
            {'id': '76679', 'name': 'Mexico City', 'country': 'Mexico', 'latitude': 19.43, 'longitude': -99.07},
            {'id': '41194', 'name': 'Dubai International', 'country': 'United Arab Emirates', 'latitude': 25.25, 'longitude': 55.36},
            {'id': '40438', 'name': 'Riyadh', 'country': 'Saudi Arabia', 'latitude': 24.71, 'longitude': 46.73},
            {'id': '62366', 'name': 'Cairo International', 'country': 'Egypt', 'latitude': 30.13, 'longitude': 31.40},
            {'id': '68816', 'name': 'Cape Town', 'country': 'South Africa', 'latitude': -33.97, 'longitude': 18.60},
            {'id': '63741', 'name': 'Nairobi', 'country': 'Kenya', 'latitude': -1.32, 'longitude': 36.92},
            {'id': '40179', 'name': 'Tel Aviv', 'country': 'Israel', 'latitude': 32.01, 'longitude': 34.89},
            {'id': '47662', 'name': 'Tokyo', 'country': 'Japan', 'latitude': 35.69, 'longitude': 139.69},
            {'id': '48698', 'name': 'Singapore Changi', 'country': 'Singapore', 'latitude': 1.36, 'longitude': 103.99},
            {'id': '45004', 'name': 'Hong Kong Observatory', 'country': 'Hong Kong', 'latitude': 22.30, 'longitude': 114.17},
            {'id': '43003', 'name': 'Mumbai', 'country': 'India', 'latitude': 19.09, 'longitude': 72.85},
            {'id': '54511', 'name': 'Beijing', 'country': 'China', 'latitude': 39.93, 'longitude': 116.28},
            {'id': '47108', 'name': 'Seoul', 'country': 'South Korea', 'latitude': 37.57, 'longitude': 126.97},
            {'id': '94767', 'name': 'Sydney', 'country': 'Australia', 'latitude': -33.95, 'longitude': 151.18},
            {'id': '83781', 'name': 'São Paulo', 'country': 'Brazil', 'latitude': -23.63, 'longitude': -46.66},
            {'id': '87576', 'name': 'Buenos Aires', 'country': 'Argentina', 'latitude': -34.58, 'longitude': -58.48},
            {'id': '84628', 'name': 'Lima', 'country': 'Peru', 'latitude': -12.02, 'longitude': -77.11}
        ]


@st.cache_data(ttl=3600)
def find_nearest_wmo_station(lat, lon):
    """Find the nearest WMO weather station for given coordinates"""
    stations = load_complete_wmo_stations()
    
    if not stations:
        return None
    
    min_distance = float('inf')
    nearest_station = None
    
    for station in stations:
        # Calculate approximate distance using Haversine formula
        dlat = lat - station['latitude']
        dlon = lon - station['longitude']
        distance = (dlat**2 + dlon**2)**0.5  # Simplified distance calculation
        
        if distance < min_distance:
            min_distance = distance
            nearest_station = station
    
    return nearest_station


def get_weather_data_from_coordinates(lat, lon, api_key):
    """Get weather data from OpenWeatherMap API using coordinates"""
    if not api_key:
        return None
    
    try:
        # Current weather data
        current_url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={api_key}&units=metric"
        response = requests.get(current_url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            return {
                'temperature': data['main']['temp'],
                'humidity': data['main']['humidity'],
                'pressure': data['main']['pressure'],
                'description': data['weather'][0]['description'],
                'wind_speed': data['wind']['speed'],
                'clouds': data['clouds']['all'],
                'visibility': data.get('visibility', 10000),
                'api_success': True
            }
        else:
            return {'api_success': False, 'error': f"API Error: {response.status_code}"}
            
    except Exception as e:
        return {'api_success': False, 'error': str(e)}


def fetch_openweather_forecast_data(lat, lon, api_key):
    """Fetch 5-day forecast data from OpenWeatherMap API for TMY generation"""
    if not api_key:
        return None
    
    try:
        # 5-day forecast with 3-hour intervals
        forecast_url = f"https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={api_key}&units=metric"
        response = requests.get(forecast_url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            forecast_data = []
            
            for item in data['list']:
                forecast_data.append({
                    'datetime': item['dt_txt'],
                    'temperature': item['main']['temp'],
                    'humidity': item['main']['humidity'],
                    'pressure': item['main']['pressure'],
                    'description': item['weather'][0]['description'],
                    'wind_speed': item['wind']['speed'],
                    'clouds': item['clouds']['all']
                })
            
            return {
                'forecast': forecast_data,
                'api_success': True
            }
        else:
            return {'api_success': False, 'error': f"API Error: {response.status_code}"}
            
    except Exception as e:
        return {'api_success': False, 'error': str(e)}


def parse_csv_content(content):
    """Parse CSV content without pandas"""
    lines = content.strip().split('\n')
    if not lines:
        return [], []
    
    # Parse headers
    headers = [h.strip() for h in lines[0].split(',')]
    
    # Parse data rows
    data = []
    for line in lines[1:]:
        if line.strip():
            # Handle quoted fields and commas within quotes
            row = []
            in_quotes = False
            current_field = ""
            
            for char in line:
                if char == '"':
                    in_quotes = not in_quotes
                elif char == ',' and not in_quotes:
                    row.append(current_field.strip())
                    current_field = ""
                else:
                    current_field += char
            
            # Add the last field
            row.append(current_field.strip())
            
            # Clean up quotes from fields
            row = [field.strip('"').strip() for field in row]
            
            if len(row) >= len(headers):
                data.append(row)
    
    return headers, data


# Database wrapper functions for easy access
def save_project_data(project_data):
    """Save project data to database"""
    return db_manager.save_project(project_data)


def save_weather_data(project_id, weather_data):
    """Save weather data to database"""
    return db_manager.save_weather_data(project_id, weather_data)


def save_building_elements(project_id, building_elements):
    """Save building elements to database"""
    return db_manager.save_building_elements(project_id, building_elements)


def save_radiation_analysis(project_id, radiation_data):
    """Save radiation analysis to database"""
    return db_manager.save_radiation_analysis(project_id, radiation_data)


def save_pv_specifications(project_id, pv_specs):
    """Save PV specifications to database"""
    return db_manager.save_pv_specifications(project_id, pv_specs)


def get_pv_specifications(project_id):
    """Get PV specifications from database"""
    return db_manager.get_pv_specifications(project_id)


def save_yield_demand_data(project_id, yield_data):
    """Save yield and demand analysis to database"""
    return db_manager.save_yield_demand_data(project_id, yield_data)


def save_optimization_results(project_id, optimization_data):
    """Save optimization results to database"""
    return db_manager.save_optimization_results(project_id, optimization_data)


def save_financial_analysis(project_id, financial_data):
    """Save financial analysis to database"""
    return db_manager.save_financial_analysis(project_id, financial_data)


def get_project_report_data(project_name):
    """Get comprehensive project data for reports"""
    return db_manager.get_project_report_data(project_name)


def list_projects():
    """List all projects in database"""
    return db_manager.list_projects()