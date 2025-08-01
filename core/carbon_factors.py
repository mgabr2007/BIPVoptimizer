"""
Grid Carbon Intensity Factors for BIPV Environmental Impact Analysis
Based on official sources: IEA, EEA, national statistics offices

Sources:
- IEA World Energy Outlook 2023
- European Environment Agency (EEA) 2023 data
- National grid operators and statistics offices
- IPCC Assessment Report 6 (AR6) electricity factors
- Live data APIs from national grid operators
"""

import streamlit as st
import requests
import json
import time
from datetime import datetime, timedelta

def fetch_live_carbon_intensity(country_code):
    """
    Fetch live carbon intensity data from official APIs
    
    Args:
        country_code (str): ISO country code (e.g., 'DE', 'GB', 'FR')
    
    Returns:
        dict: Live carbon factor data or None if fetch fails
    """
    try:
        # API mappings for live carbon intensity data
        api_configs = {
            'DE': {
                'url': 'https://www.smard.de/app/chart_data/410/DE/410_DE_quarterhour_',
                'method': 'smard_de',
                'name': 'German SMARD API'
            },
            'GB': {
                'url': 'https://api.carbonintensity.org.uk/intensity',
                'method': 'uk_carbon',
                'name': 'UK Carbon Intensity API'
            },
            'FR': {
                'url': 'https://digital.iservices.rte-france.com/open_api/co2_emission/v1/co2',
                'method': 'rte_france',
                'name': 'RTE France API'
            },
            'DK': {
                'url': 'https://api.energidataservice.dk/dataset/CO2Emis',
                'method': 'energinet_dk',
                'name': 'Energinet Denmark API'
            }
        }
        
        if country_code not in api_configs:
            return None
            
        config = api_configs[country_code]
        
        # UK Carbon Intensity API
        if config['method'] == 'uk_carbon':
            response = requests.get(config['url'], timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get('data') and len(data['data']) > 0:
                    intensity = data['data'][0]['intensity']
                    actual = intensity.get('actual') or intensity.get('forecast', 0)
                    return {
                        'factor': actual / 1000,  # Convert g/kWh to kg/kWh
                        'source': f"UK National Grid ESO (Live API) - {datetime.now().strftime('%H:%M %d/%m/%Y')}",
                        'year': datetime.now().year,
                        'confidence': 'high',
                        'region_type': 'live_api_official'
                    }
        
        # German SMARD API
        elif config['method'] == 'smard_de':
            # Use simplified approach - get recent data
            now = datetime.now()
            yesterday = now - timedelta(days=1)
            date_str = yesterday.strftime('%Y-%m-%d')
            
            # SMARD API for CO2 emissions
            url = f"https://www.smard.de/app/chart_data/1030/DE/1030_DE_quarterhour_{date_str.replace('-', '')}.json"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('series') and len(data['series']) > 0:
                    # Get latest non-null value
                    latest_values = [x[1] for x in data['series'] if x[1] is not None]
                    if latest_values:
                        co2_intensity = latest_values[-1]  # g/kWh
                        return {
                            'factor': co2_intensity / 1000,  # Convert to kg/kWh
                            'source': f"German SMARD API (Live) - {datetime.now().strftime('%H:%M %d/%m/%Y')}",
                            'year': datetime.now().year,
                            'confidence': 'high',
                            'region_type': 'live_api_official'
                        }
        
        # Add more API implementations as needed
        return None
        
    except Exception as e:
        st.warning(f"Live data fetch failed for {country_code}: {str(e)}")
        return None

def get_grid_carbon_factor(location_name, coordinates=None):
    """
    Get grid carbon intensity factor (kg CO₂/kWh) based on location
    Tries live APIs first, falls back to static data
    
    Args:
        location_name (str): Location name from project setup
        coordinates (dict): Optional lat/lon for regional estimates
    
    Returns:
        dict: {
            'factor': float,
            'source': str,
            'year': int,
            'confidence': str,
            'region_type': str
        }
    """
    
    # First, try to get live data from official APIs
    country_code = None
    location_lower = location_name.lower() if location_name else ""
    
    # Map location to country codes for API lookup - enhanced for Berlin detection
    country_mappings = {
        'germany': 'DE', 'deutschland': 'DE', 'berlin': 'DE', 'munich': 'DE', 'hamburg': 'DE',
        'cologne': 'DE', 'frankfurt': 'DE', 'düsseldorf': 'DE', 'dortmund': 'DE', 'essen': 'DE',
        'united kingdom': 'GB', 'uk': 'GB', 'britain': 'GB', 'london': 'GB', 'manchester': 'GB',
        'france': 'FR', 'paris': 'FR', 'lyon': 'FR', 'marseille': 'FR',
        'denmark': 'DK', 'copenhagen': 'DK', 'aarhus': 'DK'
    }
    
    # Debug output for Berlin detection
    if 'berlin' in location_lower:
        st.info(f"🔍 Detected Berlin in location: '{location_name}' → Country code: DE")
        print(f"DEBUG: Berlin detected in '{location_name}', setting country_code to DE")
    
    for location_key, code in country_mappings.items():
        if location_key in location_lower:
            country_code = code
            break
    
    # Try to fetch live data
    if country_code:
        live_data = fetch_live_carbon_intensity(country_code)
        if live_data:
            return live_data
    
    # Fallback to static official data if live fetch fails
    # Official grid carbon factors (kg CO₂/kWh) - 2023 data
    # Sources: IEA, EEA, national grid operators
    CARBON_FACTORS = {
        # European Union (EEA 2023 official data)
        'germany': {
            'factor': 0.434,
            'source': 'German Federal Environment Agency (UBA) 2023',
            'year': 2023,
            'confidence': 'high',
            'region_type': 'national_official'
        },
        'france': {
            'factor': 0.057,
            'source': 'RTE (French TSO) & ADEME 2023',
            'year': 2023,
            'confidence': 'high',
            'region_type': 'national_official'
        },
        'poland': {
            'factor': 0.781,
            'source': 'Polish Energy Regulatory Office 2023',
            'year': 2023,
            'confidence': 'high',
            'region_type': 'national_official'
        },
        'denmark': {
            'factor': 0.109,
            'source': 'Energinet (Danish TSO) 2023',
            'year': 2023,
            'confidence': 'high',
            'region_type': 'national_official'
        },
        'netherlands': {
            'factor': 0.311,
            'source': 'Statistics Netherlands (CBS) 2023',
            'year': 2023,
            'confidence': 'high',
            'region_type': 'national_official'
        },
        'spain': {
            'factor': 0.256,
            'source': 'Red Eléctrica de España (REE) 2023',
            'year': 2023,
            'confidence': 'high',
            'region_type': 'national_official'
        },
        'italy': {
            'factor': 0.432,
            'source': 'Terna (Italian TSO) & ISPRA 2023',
            'year': 2023,
            'confidence': 'high',
            'region_type': 'national_official'
        },
        'united kingdom': {
            'factor': 0.233,
            'source': 'National Grid ESO & DEFRA 2023',
            'year': 2023,
            'confidence': 'high',
            'region_type': 'national_official'
        },
        'austria': {
            'factor': 0.159,
            'source': 'Austrian Energy Agency 2023',
            'year': 2023,
            'confidence': 'high',
            'region_type': 'national_official'
        },
        'sweden': {
            'factor': 0.042,
            'source': 'Svenska Kraftnät 2023',
            'year': 2023,
            'confidence': 'high',
            'region_type': 'national_official'
        },
        'norway': {
            'factor': 0.024,
            'source': 'Statnett & Statistics Norway 2023',
            'year': 2023,
            'confidence': 'high',
            'region_type': 'national_official'
        },
        
        # North America
        'united states': {
            'factor': 0.421,
            'source': 'US EPA eGRID 2023',
            'year': 2023,
            'confidence': 'high',
            'region_type': 'national_official'
        },
        'canada': {
            'factor': 0.130,
            'source': 'Environment and Climate Change Canada 2023',
            'year': 2023,
            'confidence': 'high',
            'region_type': 'national_official'
        },
        
        # Middle East & Africa (IEA estimates)
        'egypt': {
            'factor': 0.532,
            'source': 'IEA World Energy Outlook 2023',
            'year': 2023,
            'confidence': 'medium',
            'region_type': 'iea_estimate'
        },
        'united arab emirates': {
            'factor': 0.491,
            'source': 'IEA World Energy Outlook 2023',
            'year': 2023,
            'confidence': 'medium',
            'region_type': 'iea_estimate'
        },
        'south africa': {
            'factor': 0.828,
            'source': 'IEA World Energy Outlook 2023',
            'year': 2023,
            'confidence': 'medium',
            'region_type': 'iea_estimate'
        },
        'morocco': {
            'factor': 0.721,
            'source': 'IEA World Energy Outlook 2023',
            'year': 2023,
            'confidence': 'medium',
            'region_type': 'iea_estimate'
        },
        
        # Asia-Pacific
        'japan': {
            'factor': 0.462,
            'source': 'Japan Electric Power Information Center 2023',
            'year': 2023,
            'confidence': 'high',
            'region_type': 'national_official'
        },
        'china': {
            'factor': 0.571,
            'source': 'IEA World Energy Outlook 2023',
            'year': 2023,
            'confidence': 'medium',
            'region_type': 'iea_estimate'
        },
        'australia': {
            'factor': 0.634,
            'source': 'Australian Energy Market Operator 2023',
            'year': 2023,
            'confidence': 'high',
            'region_type': 'national_official'
        }
    }
    
    if not location_name:
        return get_fallback_carbon_factor(coordinates)
    
    # Normalize location name for matching
    location_lower = location_name.lower()
    
    # Direct country matching
    for country, data in CARBON_FACTORS.items():
        if country in location_lower:
            return data
    
    # City-based matching
    city_mappings = {
        'berlin': 'germany',
        'munich': 'germany',
        'hamburg': 'germany',
        'frankfurt': 'germany',
        'cologne': 'germany',
        'paris': 'france',
        'lyon': 'france',
        'marseille': 'france',
        'toulouse': 'france',
        'warsaw': 'poland',
        'krakow': 'poland',
        'gdansk': 'poland',
        'copenhagen': 'denmark',
        'aarhus': 'denmark',
        'amsterdam': 'netherlands',
        'rotterdam': 'netherlands',
        'the hague': 'netherlands',
        'madrid': 'spain',
        'barcelona': 'spain',
        'valencia': 'spain',
        'rome': 'italy',
        'milan': 'italy',
        'naples': 'italy',
        'london': 'united kingdom',
        'manchester': 'united kingdom',
        'birmingham': 'united kingdom',
        'cairo': 'egypt',
        'alexandria': 'egypt',
        'giza': 'egypt',
        'dubai': 'united arab emirates',
        'abu dhabi': 'united arab emirates',
        'cape town': 'south africa',
        'johannesburg': 'south africa',
        'casablanca': 'morocco',
        'rabat': 'morocco'
    }
    
    for city, country in city_mappings.items():
        if city in location_lower:
            return CARBON_FACTORS[country]
    
    # Fallback to regional estimates
    return get_fallback_carbon_factor(coordinates, location_name)

def get_fallback_carbon_factor(coordinates=None, location_name=""):
    """
    Fallback carbon factor estimation based on coordinates or global average
    """
    
    # Regional estimates based on coordinates (IPCC AR6 regional averages)
    if coordinates and 'lat' in coordinates and 'lon' in coordinates:
        lat = coordinates['lat']
        lon = coordinates['lon']
        
        # European region
        if 35 <= lat <= 70 and -10 <= lon <= 50:
            return {
                'factor': 0.298,
                'source': 'IPCC AR6 European Regional Average',
                'year': 2023,
                'confidence': 'low',
                'region_type': 'regional_estimate'
            }
        
        # North American region
        elif 30 <= lat <= 70 and -170 <= lon <= -50:
            return {
                'factor': 0.387,
                'source': 'IPCC AR6 North American Regional Average',
                'year': 2023,
                'confidence': 'low',
                'region_type': 'regional_estimate'
            }
        
        # Middle East & North Africa
        elif 15 <= lat <= 40 and -20 <= lon <= 60:
            return {
                'factor': 0.623,
                'source': 'IPCC AR6 MENA Regional Average',
                'year': 2023,
                'confidence': 'low',
                'region_type': 'regional_estimate'
            }
        
        # Sub-Saharan Africa
        elif -35 <= lat <= 15 and -20 <= lon <= 50:
            return {
                'factor': 0.712,
                'source': 'IPCC AR6 Sub-Saharan Africa Regional Average',
                'year': 2023,
                'confidence': 'low',
                'region_type': 'regional_estimate'
            }
        
        # Asia-Pacific
        elif -50 <= lat <= 50 and 60 <= lon <= 180:
            return {
                'factor': 0.542,
                'source': 'IPCC AR6 Asia-Pacific Regional Average',
                'year': 2023,
                'confidence': 'low',
                'region_type': 'regional_estimate'
            }
    
    # Global average fallback
    return {
        'factor': 0.475,
        'source': 'IEA Global Average 2023',
        'year': 2023,
        'confidence': 'low',
        'region_type': 'global_average'
    }

def display_carbon_factor_info(carbon_data):
    """Display carbon factor information with source and confidence level"""
    
    factor = carbon_data['factor']
    source = carbon_data['source']
    confidence = carbon_data['confidence']
    region_type = carbon_data['region_type']
    
    # Color coding based on confidence
    if confidence == 'high':
        color = 'green'
        icon = '✅'
    elif confidence == 'medium':
        color = 'orange'
        icon = '⚠️'
    else:
        color = 'red'
        icon = '❓'
    
    # Region type description
    type_descriptions = {
        'live_api_official': 'Live official grid API data',
        'national_official': 'Official national grid data',
        'iea_estimate': 'IEA published estimate',
        'regional_estimate': 'IPCC regional average',
        'global_average': 'Global average fallback'
    }
    
    st.info(f"{icon} **Source**: {source}\n"
            f"**Data Type**: {type_descriptions.get(region_type, 'Estimate')}\n"
            f"**Confidence**: {confidence.title()}")
    
    if confidence == 'low':
        st.warning("⚠️ Using estimated carbon factor. For accurate analysis, please verify local grid emissions data.")
    elif region_type == 'live_api_official':
        st.success("🌐 Live carbon intensity data successfully retrieved from official grid operator API!")