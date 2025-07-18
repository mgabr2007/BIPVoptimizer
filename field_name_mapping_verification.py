"""
Field Name Mapping Verification for BIPV Workflow Steps
Ensures consistent dataflow between Step 6 and Steps 7-10
"""

import pandas as pd

# Standard field names as defined in unified Step 6
STANDARD_FIELD_NAMES = {
    'element_id': 'element_id',
    'capacity_kw': 'capacity_kw', 
    'annual_energy_kwh': 'annual_energy_kwh',
    'total_cost_eur': 'total_cost_eur',
    'glass_area_m2': 'glass_area_m2',
    'orientation': 'orientation',
    'efficiency': 'efficiency',
    'transparency': 'transparency',
    'specific_yield_kwh_kw': 'specific_yield_kwh_kw',
    'power_density_w_m2': 'power_density_w_m2'
}

# Field name variants found in workflow steps
FIELD_NAME_VARIANTS = {
    # Capacity variations
    'capacity_kw': ['capacity_kw', 'system_power_kw', 'total_power_kw', 'total_capacity_kw'],
    
    # Cost variations  
    'total_cost_eur': ['total_cost_eur', 'total_installation_cost', 'investment_cost', 'system_cost'],
    
    # Energy variations
    'annual_energy_kwh': ['annual_energy_kwh', 'annual_yield_kwh', 'energy_generation', 'annual_production'],
    
    # Area variations
    'glass_area_m2': ['glass_area_m2', 'area_m2', 'bipv_area_m2', 'system_area'],
    
    # ID variations
    'element_id': ['element_id', 'Element ID', 'system_id', 'id']
}

def create_field_mapping_function():
    """Create a standardized field mapping function for workflow consistency"""
    
    def map_field_names(df, field_mapping=None):
        """
        Map various field names to standard field names for workflow consistency
        
        Args:
            df: DataFrame with PV specifications
            field_mapping: Custom field mapping dict (optional)
        
        Returns:
            DataFrame with standardized field names
        """
        if field_mapping is None:
            field_mapping = {}
            
            # Capacity mapping
            for variant in FIELD_NAME_VARIANTS['capacity_kw']:
                if variant in df.columns:
                    field_mapping[variant] = STANDARD_FIELD_NAMES['capacity_kw']
                    break
            
            # Cost mapping  
            for variant in FIELD_NAME_VARIANTS['total_cost_eur']:
                if variant in df.columns:
                    field_mapping[variant] = STANDARD_FIELD_NAMES['total_cost_eur']
                    break
            
            # Energy mapping
            for variant in FIELD_NAME_VARIANTS['annual_energy_kwh']:
                if variant in df.columns:
                    field_mapping[variant] = STANDARD_FIELD_NAMES['annual_energy_kwh']
                    break
            
            # Area mapping
            for variant in FIELD_NAME_VARIANTS['glass_area_m2']:
                if variant in df.columns:
                    field_mapping[variant] = STANDARD_FIELD_NAMES['glass_area_m2']
                    break
                    
            # ID mapping
            for variant in FIELD_NAME_VARIANTS['element_id']:
                if variant in df.columns:
                    field_mapping[variant] = STANDARD_FIELD_NAMES['element_id']
                    break
        
        # Apply field mapping
        mapped_df = df.rename(columns=field_mapping)
        
        return mapped_df, field_mapping
    
    return map_field_names

def verify_step_compatibility(pv_specs_df):
    """
    Verify that PV specifications DataFrame is compatible with all workflow steps
    
    Args:
        pv_specs_df: DataFrame with PV specifications from Step 6
        
    Returns:
        dict: Compatibility report for each workflow step
    """
    
    compatibility_report = {
        'step_7_yield_demand': {
            'required_fields': ['capacity_kw', 'annual_energy_kwh', 'element_id'],
            'compatible': True,
            'missing_fields': [],
            'alternative_fields': []
        },
        'step_8_optimization': {
            'required_fields': ['capacity_kw', 'total_cost_eur', 'annual_energy_kwh'],
            'compatible': True,
            'missing_fields': [],
            'alternative_fields': []
        },
        'step_9_financial': {
            'required_fields': ['total_cost_eur', 'annual_energy_kwh', 'capacity_kw'],
            'compatible': True,
            'missing_fields': [],
            'alternative_fields': []
        },
        'step_10_dashboard': {
            'required_fields': ['element_id', 'capacity_kw', 'total_cost_eur', 'glass_area_m2'],
            'compatible': True,
            'missing_fields': [],
            'alternative_fields': []
        }
    }
    
    # Check compatibility for each step
    for step_name, step_info in compatibility_report.items():
        for required_field in step_info['required_fields']:
            
            # Check if field exists directly
            if required_field in pv_specs_df.columns:
                continue
            
            # Check if alternative field names exist
            field_found = False
            if required_field in FIELD_NAME_VARIANTS:
                for variant in FIELD_NAME_VARIANTS[required_field]:
                    if variant in pv_specs_df.columns:
                        step_info['alternative_fields'].append(f"{required_field} -> {variant}")
                        field_found = True
                        break
            
            if not field_found:
                step_info['missing_fields'].append(required_field)
                step_info['compatible'] = False
    
    return compatibility_report

def generate_compatibility_report(pv_specs_df):
    """Generate a comprehensive compatibility report"""
    
    print("=== BIPV Workflow Field Name Compatibility Report ===\n")
    
    print("Available fields in PV specifications:")
    for col in pv_specs_df.columns:
        print(f"  - {col}")
    print()
    
    compatibility = verify_step_compatibility(pv_specs_df)
    
    for step_name, step_info in compatibility.items():
        status = "✅ COMPATIBLE" if step_info['compatible'] else "❌ INCOMPATIBLE"
        print(f"{step_name.upper()}: {status}")
        
        if step_info['missing_fields']:
            print(f"  Missing fields: {', '.join(step_info['missing_fields'])}")
        
        if step_info['alternative_fields']:
            print(f"  Alternative mappings: {', '.join(step_info['alternative_fields'])}")
        
        print()

if __name__ == "__main__":
    # Test with sample data
    sample_data = pd.DataFrame({
        'element_id': ['E001', 'E002', 'E003'],
        'capacity_kw': [2.5, 3.1, 1.8],
        'annual_energy_kwh': [3200, 3900, 2300],
        'total_cost_eur': [8750, 10850, 6300],
        'glass_area_m2': [15.2, 18.3, 11.1]
    })
    
    generate_compatibility_report(sample_data)