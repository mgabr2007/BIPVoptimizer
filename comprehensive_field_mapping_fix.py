"""
Comprehensive Field Mapping Fix for BIPV Workflow
Identifies and fixes ALL field name mismatches across Steps 6-10
"""

import pandas as pd

# Complete mapping of ALL field variations found in the codebase
FIELD_MAPPING = {
    # Power/Capacity field variations
    'capacity_kw': ['capacity_kw', 'system_power_kw', 'total_power_kw', 'total_capacity_kw'],
    
    # Cost field variations
    'total_cost_eur': ['total_cost_eur', 'total_installation_cost', 'total_investment', 'total_cost', 'investment_cost'],
    
    # Energy field variations
    'annual_energy_kwh': ['annual_energy_kwh', 'annual_yield_kwh', 'energy_generation', 'annual_production'],
    
    # Area field variations
    'glass_area_m2': ['glass_area_m2', 'glass_area', 'area_m2', 'bipv_area_m2', 'bipv_area'],
    
    # Element ID variations
    'element_id': ['element_id', 'Element_ID', 'ElementId', 'Element ID', 'system_id']
}

def standardize_pv_specifications_dataframe(df):
    """
    Standardize ANY PV specifications DataFrame to use consistent field names
    This ensures compatibility across ALL workflow steps
    """
    if df is None or len(df) == 0:
        return df
        
    # Create a copy to avoid modifying original
    standardized_df = df.copy()
    
    # Apply field mapping for each standard field
    for standard_field, variations in FIELD_MAPPING.items():
        # Find which variation exists in the DataFrame
        found_field = None
        for variation in variations:
            if variation in standardized_df.columns:
                found_field = variation
                break
        
        # Rename to standard field name if needed
        if found_field and found_field != standard_field:
            standardized_df = standardized_df.rename(columns={found_field: standard_field})
            print(f"Mapped {found_field} → {standard_field}")
    
    return standardized_df

def verify_field_compatibility(df, step_name="unknown"):
    """Verify that DataFrame has all required fields for workflow steps"""
    
    required_fields = {
        'step_7_yield': ['capacity_kw', 'annual_energy_kwh', 'element_id'],
        'step_8_optimization': ['capacity_kw', 'total_cost_eur', 'annual_energy_kwh'],
        'step_9_financial': ['total_cost_eur', 'annual_energy_kwh', 'capacity_kw'],
        'step_10_dashboard': ['element_id', 'capacity_kw', 'total_cost_eur', 'glass_area_m2']
    }
    
    missing_fields = []
    for step, fields in required_fields.items():
        step_missing = []
        for field in fields:
            if field not in df.columns:
                step_missing.append(field)
        if step_missing:
            missing_fields.append(f"{step}: missing {step_missing}")
    
    if missing_fields:
        print(f"WARNING - {step_name} compatibility issues:")
        for issue in missing_fields:
            print(f"  {issue}")
        return False
    else:
        print(f"✅ {step_name} - All field compatibility verified")
        return True

if __name__ == "__main__":
    # Test with sample problematic data
    sample_problematic_data = pd.DataFrame({
        'element_id': ['E001', 'E002'],
        'system_power_kw': [2.5, 3.1],  # Should be capacity_kw
        'annual_yield_kwh': [3200, 3900],  # Should be annual_energy_kwh
        'total_installation_cost': [8750, 10850],  # Should be total_cost_eur
        'glass_area': [15.2, 18.3]  # Should be glass_area_m2
    })
    
    print("BEFORE standardization:")
    verify_field_compatibility(sample_problematic_data, "Original Data")
    
    print("\nApplying field mapping...")
    standardized_data = standardize_pv_specifications_dataframe(sample_problematic_data)
    
    print("\nAFTER standardization:")
    verify_field_compatibility(standardized_data, "Standardized Data")
    
    print(f"\nFinal standardized columns: {list(standardized_data.columns)}")