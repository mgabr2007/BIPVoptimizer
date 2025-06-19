import streamlit as st
import uuid
from datetime import datetime
import pytz

def render_project_setup():
    """Render the project setup module with configuration inputs."""
    
    st.header("1. Project Setup")
    st.markdown("Configure your BIPV analysis project with basic settings and upload BIM models.")
    
    # Project configuration section
    st.subheader("Project Configuration")
    
    col1, col2 = st.columns(2)
    
    with col1:
        project_name = st.text_input(
            "Project Name", 
            value=st.session_state.project_data.get('project_name', ''),
            help="Enter a descriptive name for your BIPV analysis project"
        )
        
        # Timezone selection
        timezones = [tz for tz in pytz.all_timezones if '/' in tz]
        timezone = st.selectbox(
            "Timezone",
            timezones,
            index=timezones.index(st.session_state.project_data.get('timezone', 'UTC')) if st.session_state.project_data.get('timezone') in timezones else 0,
            help="Select the timezone for your project location"
        )
        
        # Units system
        units = st.selectbox(
            "Units System",
            ["Metric (SI)", "Imperial (US)", "Mixed"],
            index=["Metric (SI)", "Imperial (US)", "Mixed"].index(st.session_state.project_data.get('units', 'Metric (SI)')),
            help="Choose the unit system for measurements and calculations"
        )
    
    with col2:
        # Currency selection
        currencies = ["USD", "EUR", "GBP", "JPY", "CAD", "AUD", "CHF", "CNY", "INR", "BRL"]
        currency = st.selectbox(
            "Currency",
            currencies,
            index=currencies.index(st.session_state.project_data.get('currency', 'USD')) if st.session_state.project_data.get('currency') in currencies else 0,
            help="Select the currency for financial calculations"
        )
        
        # Language selection
        languages = ["English", "Spanish", "French", "German", "Italian", "Portuguese", "Chinese", "Japanese"]
        language = st.selectbox(
            "Language",
            languages,
            index=languages.index(st.session_state.project_data.get('language', 'English')) if st.session_state.project_data.get('language') in languages else 0,
            help="Select the language for reports and interface"
        )
        
        # Generate or display Project ID
        if 'project_id' not in st.session_state.project_data:
            project_id = str(uuid.uuid4())[:8]
            st.session_state.project_data['project_id'] = project_id
        else:
            project_id = st.session_state.project_data['project_id']
        
        st.text_input(
            "Project ID",
            value=project_id,
            disabled=True,
            help="Unique identifier for this project (auto-generated)"
        )
    
    # BIM Model Upload Section
    st.subheader("BIM Model Upload")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**LOD 200 Model (Detailed)**")
        lod200_file = st.file_uploader(
            "Upload Revit Model (.rvt)",
            type=['rvt'],
            key="lod200_uploader",
            help="Upload the detailed BIM model (LOD 200) for facade analysis"
        )
        
        if lod200_file is not None:
            st.success(f"✅ LOD 200 model uploaded: {lod200_file.name}")
            st.session_state.project_data['lod200_model'] = {
                'name': lod200_file.name,
                'size': lod200_file.size,
                'type': lod200_file.type
            }
            
            # Display file info
            st.info(f"File size: {lod200_file.size / 1024 / 1024:.2f} MB")
    
    with col2:
        st.markdown("**LOD 100 Context Model (Simplified)**")
        lod100_file = st.file_uploader(
            "Upload Context Model (.rvt)",
            type=['rvt'],
            key="lod100_uploader",
            help="Upload the context BIM model (LOD 100) for environmental analysis"
        )
        
        if lod100_file is not None:
            st.success(f"✅ LOD 100 context model uploaded: {lod100_file.name}")
            st.session_state.project_data['lod100_model'] = {
                'name': lod100_file.name,
                'size': lod100_file.size,
                'type': lod100_file.type
            }
            
            # Display file info
            st.info(f"File size: {lod100_file.size / 1024 / 1024:.2f} MB")
    
    # Save configuration
    st.session_state.project_data.update({
        'project_name': project_name,
        'timezone': timezone,
        'units': units,
        'currency': currency,
        'language': language,
        'created_date': datetime.now().isoformat()
    })
    
    # Display current settings
    st.subheader("Current Project Settings")
    
    if project_name:
        settings_data = {
            "Setting": ["Project Name", "Project ID", "Timezone", "Units", "Currency", "Language"],
            "Value": [
                project_name,
                project_id,
                timezone,
                units,
                currency,
                language
            ]
        }
        
        st.table(settings_data)
        
        # Model status
        st.subheader("Model Upload Status")
        
        model_status = []
        if 'lod200_model' in st.session_state.project_data:
            model_status.append({"Model": "LOD 200 (Detailed)", "Status": "✅ Uploaded", "Filename": st.session_state.project_data['lod200_model']['name']})
        else:
            model_status.append({"Model": "LOD 200 (Detailed)", "Status": "❌ Not uploaded", "Filename": "-"})
        
        if 'lod100_model' in st.session_state.project_data:
            model_status.append({"Model": "LOD 100 (Context)", "Status": "✅ Uploaded", "Filename": st.session_state.project_data['lod100_model']['name']})
        else:
            model_status.append({"Model": "LOD 100 (Context)", "Status": "❌ Not uploaded", "Filename": "-"})
        
        st.table(model_status)
        
        # Validation
        if all(key in st.session_state.project_data for key in ['project_name', 'lod200_model']):
            st.success("✅ Project setup is complete! You can proceed to the next step.")
        else:
            st.warning("⚠️ Please complete all required fields and upload at least the LOD 200 model before proceeding.")
    else:
        st.info("👆 Please enter a project name to begin configuration.")
