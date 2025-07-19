#!/usr/bin/env python3
"""
Comprehensive test of data flow from Steps 5-6 to Steps 10-11
Tests the database-driven architecture and Step 2 integration
"""

import streamlit as st
from database_manager import BIPVDatabaseManager
from services.io import get_current_project_id

def test_data_flow():
    """Test comprehensive data flow across workflow steps"""
    
    print("🔍 Testing Comprehensive Data Flow for Steps 5-6 → Steps 10-11")
    print("=" * 70)
    
    db_manager = BIPVDatabaseManager()
    
    # Test 1: Project ID resolution
    print("Test 1: Project ID Resolution")
    project_id = get_current_project_id()
    print(f"  Project ID: {project_id}")
    
    if not project_id:
        print("  ❌ No project ID found - checking for projects in database")
        with db_manager.get_connection().cursor() as cursor:
            cursor.execute("SELECT id, project_name FROM projects ORDER BY created_at DESC LIMIT 5")
            projects = cursor.fetchall()
            print(f"  Available projects: {projects}")
            if projects:
                project_id = projects[0][0]
                print(f"  Using first project: {project_id}")
    
    if not project_id:
        print("  ❌ No projects found in database")
        return
        
    print(f"  ✅ Using project ID: {project_id}")
    print()
    
    # Test 2: Step 2 AI Model Data
    print("Test 2: Step 2 AI Model Data Integration")
    try:
        with db_manager.get_connection().cursor() as cursor:
            cursor.execute("""
                SELECT model_type, r_squared_score, training_data_size, 
                       building_area, growth_rate, base_consumption, peak_demand
                FROM ai_models WHERE project_id = %s 
                ORDER BY created_at DESC LIMIT 1
            """, (project_id,))
            ai_model = cursor.fetchone()
            
            if ai_model:
                print(f"  ✅ AI Model Found:")
                print(f"    Model Type: {ai_model[0]}")
                print(f"    R² Score: {ai_model[1]}")
                print(f"    Training Data Size: {ai_model[2]}")
                print(f"    Building Area: {ai_model[3]} m²")
                print(f"    Growth Rate: {ai_model[4]}%")
                print(f"    Base Consumption: {ai_model[5]} kWh")
                print(f"    Peak Demand: {ai_model[6]} kW")
            else:
                print("  ❌ No AI model data found")
    except Exception as e:
        print(f"  ❌ Error querying AI model: {e}")
    print()
    
    # Test 3: Step 5 Radiation Analysis Data
    print("Test 3: Step 5 Radiation Analysis Data")
    try:
        radiation_data = db_manager.get_radiation_analysis_data(project_id)
        if radiation_data and 'element_radiation' in radiation_data:
            radiation_records = radiation_data['element_radiation']
            print(f"  ✅ Radiation Records: {len(radiation_records)}")
            if radiation_records:
                sample = radiation_records[0]
                print(f"    Sample Record: Element {sample.get('element_id')}, Radiation: {sample.get('annual_radiation')} kWh/m²/year")
        else:
            print("  ❌ No radiation analysis data found")
    except Exception as e:
        print(f"  ❌ Error querying radiation data: {e}")
    print()
    
    # Test 4: Step 6 PV Specifications Data
    print("Test 4: Step 6 PV Specifications Data")
    try:
        pv_data = db_manager.get_pv_specifications(project_id)
        if pv_data and 'bipv_specifications' in pv_data:
            bipv_specs = pv_data['bipv_specifications']
            print(f"  ✅ BIPV Specifications: {len(bipv_specs)} systems")
            if bipv_specs:
                sample = bipv_specs[0]
                print(f"    Sample System: Element {sample.get('element_id')}")
                print(f"    Capacity: {sample.get('capacity_kw')} kW")
                print(f"    Annual Energy: {sample.get('annual_energy_kwh')} kWh")
                print(f"    Total Cost: €{sample.get('total_cost_eur')}")
        else:
            print("  ❌ No PV specifications data found")
            
        # Check raw database table
        with db_manager.get_connection().cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM pv_specifications WHERE project_id = %s", (project_id,))
            count = cursor.fetchone()[0]
            print(f"    Raw PV table count: {count}")
            
    except Exception as e:
        print(f"  ❌ Error querying PV data: {e}")
    print()
    
    # Test 5: Building Elements Count
    print("Test 5: Building Elements Data")
    try:
        building_elements = db_manager.get_building_elements(project_id)
        if building_elements:
            suitable_count = sum(1 for elem in building_elements if elem.get('pv_suitable', False))
            print(f"  ✅ Building Elements: {len(building_elements)} total, {suitable_count} suitable")
        else:
            print("  ❌ No building elements found")
    except Exception as e:
        print(f"  ❌ Error querying building elements: {e}")
    print()
    
    # Test 6: Step 10 Dashboard Data Loading
    print("Test 6: Step 10 Dashboard Data Integration")
    try:
        from pages_modules.comprehensive_dashboard import get_dashboard_data
        dashboard_data = get_dashboard_data(project_id)
        
        if dashboard_data:
            print(f"  ✅ Dashboard Data Available:")
            print(f"    Project: {'✅' if 'project' in dashboard_data else '❌'}")
            print(f"    AI Model: {'✅' if 'ai_model' in dashboard_data else '❌'}")
            print(f"    Weather: {'✅' if 'weather' in dashboard_data else '❌'}")
            print(f"    Building: {'✅' if 'building' in dashboard_data else '❌'}")
            print(f"    PV Systems: {'✅' if 'pv_systems' in dashboard_data else '❌'}")
            
            if 'ai_model' in dashboard_data:
                ai = dashboard_data['ai_model']
                print(f"    AI Model R²: {ai.get('r2_score', 0)}")
                print(f"    Building Area: {ai.get('building_area', 0)} m²")
        else:
            print("  ❌ No dashboard data available")
    except Exception as e:
        print(f"  ❌ Error loading dashboard data: {e}")
    print()
    
    print("🎯 Data Flow Test Complete")
    print("=" * 70)

if __name__ == "__main__":
    test_data_flow()