"""
Welcome page for BIPV Optimizer
"""
import streamlit as st
from utils.color_schemes import get_emoji, create_colored_html, YELLOW_SCHEME


def render_welcome():
    """Render the welcome and introduction page"""
    

    
    st.markdown(f"""
    ---
    
    ### {get_emoji('sun')} Welcome to the BIPV Optimizer Platform {get_emoji('building')}
    
    **Building-Integrated Photovoltaics (BIPV)** represents the future of sustainable architecture, 
    where solar energy generation seamlessly integrates with building design. Our platform provides 
    comprehensive analysis and optimization tools for BIPV installations, specifically focusing on 
    **semi-transparent PV glass replacement** in educational and commercial buildings.
    """)
    
    # Apply yellow container styling
    st.markdown('<div class="yellow-container">', unsafe_allow_html=True)
    
    # Core BIPV Technology Explanation
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("""
        #### What is BIPV Glass Replacement?
        
        BIPV glass replacement involves **substituting conventional window glass** with semi-transparent 
        photovoltaic panels that serve dual functions:
        
        1. **Energy Generation:** Convert sunlight into electricity
        2. **Building Function:** Maintain natural lighting and weather protection
        3. **Aesthetic Integration:** Preserve architectural design integrity
        
        Our platform specifically analyzes **window-to-BIPV conversions** where existing glass areas 
        are replaced with semi-transparent PV modules, optimizing both energy performance and 
        building functionality.
        """)
    
    with col2:
        st.info("""
        **Key Benefits:**
        
        ✅ **Dual Functionality**  
        Glass + Energy Generation
        
        ✅ **Space Efficiency**  
        No additional roof area needed
        
        ✅ **Cost Optimization**  
        Replace existing glass costs
        
        ✅ **Aesthetic Integration**  
        Seamless architectural design
        """)
    
    # Workflow Overview  
    st.markdown("""
    ---
    
    ### 11-Step Analysis Workflow
    
    Our comprehensive workflow guides you through the complete BIPV analysis process:
    """)
    
    # Create workflow visualization
    workflow_steps = [
        ("1️⃣", "Project Setup", "Location, timezone, and project configuration"),
        ("2️⃣", "Historical Data", "Energy consumption analysis and AI model training"), 
        ("3️⃣", "Weather Integration", "TMY data generation and climate analysis"),
        ("4️⃣", "BIM Extraction", "Building geometry and window element analysis"),
        ("5️⃣", "Radiation Analysis", "Solar irradiance and shading calculations"),
        ("6️⃣", "PV Specification", "BIPV technology selection and system design"),
        ("7️⃣", "Yield vs Demand", "Energy balance and grid interaction analysis"),
        ("8️⃣", "Optimization", "Multi-objective genetic algorithm optimization"),
        ("9️⃣", "Financial Analysis", "Economic viability and investment analysis"),
        ("🔟", "Reporting", "Comprehensive analysis reports and data export"),
        ("🤖", "AI Consultation", "Expert analysis and optimization recommendations")
    ]
    
    # Display workflow in columns
    col1, col2 = st.columns(2)
    
    with col1:
        for i in range(0, len(workflow_steps), 2):
            step_emoji, step_name, step_desc = workflow_steps[i]
            st.markdown(f"""
            **{step_emoji} {step_name}**  
            {step_desc}
            """)
    
    with col2:
        for i in range(1, len(workflow_steps), 2):
            if i < len(workflow_steps):
                step_emoji, step_name, step_desc = workflow_steps[i]
                st.markdown(f"""
                **{step_emoji} {step_name}**  
                {step_desc}
                """)

    # Scientific Methodology
    st.markdown("""
    ---
    
    ### Scientific Methodology & Standards
    
    Our analysis platform implements **internationally recognized standards** and research-based methodologies:
    """)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"""
        **{get_emoji('tools')} ISO Standards**
        - ISO 15927-4: TMY data
        - ISO 9060: Solar radiation
        - ISO 50001: Energy management
        """)
    
    with col2:
        st.markdown("""
        **📊 ASHRAE Guidelines**
        - 90.1: Energy efficiency
        - 189.1: Green buildings
        - 62.1: Ventilation standards
        """)
    
    with col3:
        st.markdown("""
        **⚡ IEC Standards**
        - IEC 61853: PV performance
        - IEC 61730: Safety standards
        - IEC 62446: Grid connection
        """)
    
    # Research Context
    st.markdown("""
    ---
    
    ### Research Context
    
    This platform is developed as part of **PhD research at Technische Universität Berlin**, 
    focusing on optimizing BIPV integration in educational buildings. The research combines:
    
    - **Building Information Modeling (BIM)** integration for precise geometry analysis
    - **Multi-objective optimization** using genetic algorithms (NSGA-II)
    - **Machine learning** for energy demand prediction
    - **Financial modeling** with lifecycle cost analysis
    - **Environmental impact** assessment and CO₂ savings quantification
    """)
    

    
    # Platform Features
    st.markdown("""
    ---
    
    ### Platform Features
    """)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        **🏗️ BIM Integration**
        - Revit model processing
        - Window element extraction
        - Geometry analysis
        - Orientation calculations
        """)
    
    with col2:
        st.markdown("""
        **🌤️ Weather Analysis**
        - OpenWeatherMap API
        - TMY data generation
        - Solar radiation modeling
        - Climate factor integration
        """)
    
    with col3:
        st.markdown("""
        **🤖 AI Consultation**
        - Perplexity AI research agent
        - Expert analysis and recommendations
        - Current industry standards (2023-2025)
        - Optimization suggestions
        """)
    
    # Additional Features Section
    st.markdown("""
    ---
    
    ### Enhanced Platform Capabilities
    """)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        **🔧 Optimization Engine**
        - Genetic algorithms (NSGA-II)
        - Multi-objective optimization
        - Pareto frontier analysis
        - Solution comparison
        """)
    
    with col2:
        st.markdown("""
        **📊 Data Management**
        - PostgreSQL database persistence
        - Project save/load functionality
        - Comprehensive data export (CSV/HTML)
        - Session state restoration
        """)
    
    with col3:
        st.markdown("""
        **📈 Advanced Analytics**
        - Interactive visualizations (Plotly)
        - R² score performance tracking
        - Financial projections (25-year)
        - CO₂ impact assessment
        """)
    
    # Getting Started
    st.markdown("""
    ---
    
    ### Ready to Begin Your BIPV Analysis?
    
    Navigate to **Step 1: Project Setup** in the sidebar to start your comprehensive BIPV optimization study. 
    The platform implements ISO 15927-4, ISO 9060, EN 410, and ASHRAE 90.1 standards throughout the 
    11-step workflow for scientifically validated results.
    
    **Important:** Complete each step in sequence - Step 4 (BIM Extraction) is mandatory for all subsequent analyses.
    
    **New Feature:** Step 11 includes AI consultation powered by Perplexity research agent for expert analysis and optimization recommendations.
    """)
    
    # Mathematical Foundations
    st.markdown("""
    ---
    
    ### Mathematical Foundations & Recent Enhancements
    
    The platform implements comprehensive mathematical models with recent improvements:
    """)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        **Core Calculations:**
        - Solar position algorithms (ISO 15927-4)
        - Irradiance modeling with orientation corrections
        - BIPV glass technology specifications (2-12% efficiency)
        - Financial analysis (NPV, IRR, payback period)
        - Environmental impact (CO₂ savings quantification)
        """)
    
    with col2:
        st.markdown("""
        **Recent Improvements:**
        - Enhanced R² score tracking and performance indicators
        - Interactive visualization with authentic workflow data
        - Decimal-to-float conversion for database operations
        - AI-powered research consultation integration
        - Corrected navigation for 11-step workflow
        """)
    

    
    # Research Attribution
    st.markdown("""
    ---
    
    ### Research Attribution
    
    **Developed by:** Mostafa Gabr  
    **Institution:** Technische Universität Berlin  
    **Research Focus:** Building-Integrated Photovoltaics Optimization  
    **Contact:** [ResearchGate Profile](https://www.researchgate.net/profile/Mostafa-Gabr-4)
    """)