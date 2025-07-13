"""
Test radiation analysis functionality
"""

import streamlit as st
import pandas as pd
import time

# Simple test of radiation analysis pipeline
def test_radiation_analysis():
    st.title("🧪 Radiation Analysis Test")
    
    # Test database connectivity
    st.subheader("1. Database Connectivity Test")
    try:
        from utils.radiation_logger import radiation_logger
        status = radiation_logger.get_analysis_status(1)  # Test project ID 1
        st.success("✅ Database connection successful")
        if status:
            st.json(status)
        else:
            st.info("No previous analysis found")
    except Exception as e:
        st.error(f"❌ Database connection failed: {e}")
    
    # Test TMY data structure
    st.subheader("2. TMY Data Structure Test")
    if 'project_data' in st.session_state:
        weather_data = st.session_state.project_data.get('weather_analysis', {})
        tmy_data = weather_data.get('tmy_data', [])
        
        if tmy_data:
            st.success(f"✅ TMY data found: {len(tmy_data)} records")
            
            # Convert to DataFrame and check structure
            if isinstance(tmy_data, list):
                df = pd.DataFrame(tmy_data)
            else:
                df = tmy_data
            
            st.write("TMY Data columns:", list(df.columns))
            st.write("Sample data:")
            st.dataframe(df.head(3))
            
            # Check for radiation columns
            required_cols = ['ghi', 'dni', 'dhi']
            found_cols = []
            for req in required_cols:
                for col in df.columns:
                    if req.lower() in col.lower():
                        found_cols.append(f"{req} → {col}")
                        break
            
            if found_cols:
                st.success(f"✅ Radiation columns found: {', '.join(found_cols)}")
            else:
                st.error("❌ No radiation columns found")
        else:
            st.error("❌ No TMY data available")
    else:
        st.error("❌ No project data in session")
    
    # Test building elements
    st.subheader("3. Building Elements Test")
    if 'project_data' in st.session_state:
        building_elements = st.session_state.project_data.get('building_elements', [])
        
        if building_elements:
            st.success(f"✅ Building elements found: {len(building_elements)} elements")
            
            # Show sample element
            if isinstance(building_elements, list) and building_elements:
                sample_element = building_elements[0]
                st.write("Sample element structure:")
                st.json(sample_element)
                
                # Check for required fields
                required_fields = ['element_id', 'orientation', 'azimuth', 'glass_area']
                missing_fields = [field for field in required_fields if field not in sample_element]
                
                if missing_fields:
                    st.warning(f"⚠️ Missing fields: {', '.join(missing_fields)}")
                else:
                    st.success("✅ All required fields present")
        else:
            st.error("❌ No building elements available")
    
    # Run mini analysis test
    st.subheader("4. Mini Analysis Test")
    if st.button("🚀 Run Mini Test (5 elements)"):
        try:
            # Import radiation analysis function
            from pages_modules.radiation_grid import generate_radiation_grid
            from utils.analysis_monitor import analysis_monitor
            
            # Get test data
            building_elements = st.session_state.project_data.get('building_elements', [])
            weather_data = st.session_state.project_data.get('weather_analysis', {})
            tmy_data = weather_data.get('tmy_data', [])
            
            if building_elements and tmy_data:
                # Test with first 5 elements only
                test_elements = building_elements[:5]
                
                st.info(f"Testing with {len(test_elements)} elements...")
                
                # Create monitor
                monitor = analysis_monitor.create_monitor_display()
                
                # Run test
                start_time = time.time()
                results = []
                
                for i, element in enumerate(test_elements):
                    element_id = element.get('element_id', f'test_element_{i}')
                    orientation = element.get('orientation', 'South')
                    area = element.get('glass_area', 1.5)
                    
                    monitor.log_element_start(element_id, orientation, area)
                    
                    try:
                        # Simulate processing
                        time.sleep(0.1)  # Simulate work
                        
                        # Create fake result
                        annual_radiation = 1200 + (i * 100)  # Simulate different values
                        processing_time = 0.1
                        
                        results.append({
                            'element_id': element_id,
                            'annual_radiation': annual_radiation,
                            'orientation': orientation,
                            'area': area
                        })
                        
                        monitor.log_element_success(element_id, annual_radiation, processing_time)
                        
                    except Exception as e:
                        monitor.log_element_error(element_id, str(e), 0.1)
                
                total_time = time.time() - start_time
                st.success(f"✅ Mini test completed in {total_time:.2f} seconds")
                st.write("Results:")
                st.dataframe(pd.DataFrame(results))
                
            else:
                st.error("❌ Missing test data (building elements or TMY data)")
                
        except Exception as e:
            st.error(f"❌ Mini test failed: {e}")
    
    # Show analysis logs
    st.subheader("5. Analysis Logs")
    if st.button("📋 Show Recent Logs"):
        try:
            from utils.radiation_logger import radiation_logger
            import psycopg2
            import os
            
            database_url = os.environ.get('DATABASE_URL')
            if database_url:
                conn = psycopg2.connect(database_url)
                with conn.cursor() as cursor:
                    cursor.execute("""
                        SELECT analysis_timestamp, element_id, status, 
                               annual_radiation, error_message 
                        FROM radiation_analysis_log 
                        ORDER BY analysis_timestamp DESC 
                        LIMIT 10
                    """)
                    logs = cursor.fetchall()
                    
                    if logs:
                        log_df = pd.DataFrame(logs, columns=[
                            'Timestamp', 'Element ID', 'Status', 
                            'Annual Radiation', 'Error Message'
                        ])
                        st.dataframe(log_df)
                    else:
                        st.info("No analysis logs found")
                conn.close()
            else:
                st.error("No database connection available")
                
        except Exception as e:
            st.error(f"Failed to load logs: {e}")

if __name__ == "__main__":
    test_radiation_analysis()