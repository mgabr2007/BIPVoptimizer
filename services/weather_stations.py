"""
Weather Station Management for BIPV Optimizer
Handles loading and processing of WMO weather stations data
"""

import pandas as pd
import math
import streamlit as st


@st.cache_data(ttl=3600)
def load_climat_stations():
    """Load CLIMAT weather stations from the attached file with robust encoding handling."""
    
    file_path = "attached_assets/stations_list_CLIMAT_data_1751033044586.txt"
    
    # Try multiple encodings for robust file reading
    encodings = ['utf-8', 'latin-1', 'iso-8859-1', 'cp1252', 'ascii']
    
    for encoding in encodings:
        try:
            # Read the file with current encoding
            with open(file_path, 'r', encoding=encoding) as f:
                lines = f.readlines()
            
            # Parse the station data
            stations = []
            for line in lines[1:]:  # Skip header
                if line.strip():  # Skip empty lines
                    parts = line.strip().split(';')
                    if len(parts) >= 6:
                        try:
                            station = {
                                'wmo_id': parts[0].strip(),
                                'name': parts[1].strip(),
                                'latitude': float(parts[2].strip()),
                                'longitude': float(parts[3].strip()),
                                'height': float(parts[4].strip()) if parts[4].strip() else 0,
                                'country': parts[5].strip()
                            }
                            stations.append(station)
                        except (ValueError, IndexError):
                            continue  # Skip malformed lines
            
            if stations:
                return pd.DataFrame(stations)
                
        except (UnicodeDecodeError, FileNotFoundError) as e:
            continue
    
    # Fallback if file cannot be read - return empty DataFrame
    return pd.DataFrame(columns=['wmo_id', 'name', 'latitude', 'longitude', 'height', 'country'])


def calculate_distance(lat1, lon1, lat2, lon2):
    """Calculate distance between two points using Haversine formula."""
    
    # Convert latitude and longitude from degrees to radians
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    
    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    
    # Radius of earth in kilometers
    r = 6371
    distance = c * r
    
    return distance


def find_nearest_stations(target_lat, target_lon, max_distance_km=500, max_stations=10):
    """Find nearest weather stations within specified distance."""
    
    stations_df = load_climat_stations()
    
    if stations_df.empty:
        return pd.DataFrame()
    
    # Calculate distances to all stations
    stations_df['distance_km'] = stations_df.apply(
        lambda row: calculate_distance(target_lat, target_lon, row['latitude'], row['longitude']), 
        axis=1
    )
    
    # Filter by maximum distance and sort by distance
    nearby_stations = stations_df[stations_df['distance_km'] <= max_distance_km].copy()
    nearby_stations = nearby_stations.sort_values('distance_km').head(max_stations)
    
    return nearby_stations


def get_station_summary(stations_df):
    """Get summary statistics of available stations."""
    
    if stations_df.empty:
        return {
            'total_stations': 0,
            'countries': [],
            'avg_distance': 0,
            'closest_distance': 0
        }
    
    return {
        'total_stations': len(stations_df),
        'countries': sorted(stations_df['country'].unique().tolist()),
        'avg_distance': stations_df['distance_km'].mean(),
        'closest_distance': stations_df['distance_km'].min()
    }


def format_station_display(station_row):
    """Format station information for display."""
    
    return {
        'display_name': f"{station_row['name']} ({station_row['country']})",
        'wmo_id': station_row['wmo_id'],
        'coordinates': f"{station_row['latitude']:.2f}, {station_row['longitude']:.2f}",
        'distance': f"{station_row['distance_km']:.1f} km",
        'elevation': f"{station_row['height']:.0f} m",
        'full_info': f"{station_row['name']}, {station_row['country']} - {station_row['distance_km']:.1f} km away"
    }