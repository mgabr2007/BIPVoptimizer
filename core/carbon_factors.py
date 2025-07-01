"""
Grid Carbon Intensity Factors for BIPV Environmental Impact Analysis
Based on official sources: IEA, EEA, national statistics offices

Sources:
- IEA World Energy Outlook 2023
- European Environment Agency (EEA) 2023 data
- National grid operators and statistics offices
- IPCC Assessment Report 6 (AR6) electricity factors
"""

import streamlit as st

def get_grid_carbon_factor(location_name, coordinates=None):
    """
    Get grid carbon intensity factor (kg CO₂/kWh) based on location
    
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