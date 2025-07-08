"""
Welcome page for BIPV Optimizer
"""
import streamlit as st
from utils.color_schemes import get_emoji, create_colored_html, YELLOW_SCHEME


def render_welcome():
    """Render the welcome and introduction page"""
    

    
    # Main banner with professional styling
    st.markdown("""
    <div style="background: linear-gradient(135deg, #2E8B57 0%, #228B22 50%, #32CD32 100%); 
                padding: 30px; border-radius: 15px; text-align: center; margin-bottom: 30px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.2);">
        <h1 style="color: white; margin: 0; font-size: 2.5em; text-shadow: 2px 2px 4px rgba(0,0,0,0.3);">
            🌟 BIPV Optimizer Platform 🏢
        </h1>
        <p style="color: white; font-size: 1.2em; margin: 10px 0 0 0; opacity: 0.9;">
            Advanced Building-Integrated Photovoltaics Analysis & Optimization
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown(f"""
    ### {get_emoji('sun')} Transforming Buildings Into Energy Producers
    
    **Building-Integrated Photovoltaics (BIPV)** represents the cutting-edge convergence of sustainable 
    architecture and renewable energy technology. Unlike traditional rooftop solar panels, BIPV systems 
    replace conventional building materials with photovoltaic elements that serve dual functions: 
    **structural building components** and **energy generators**.
    
    Our platform specializes in **semi-transparent PV glass replacement** for educational and commercial 
    buildings, where existing windows are upgraded with advanced photovoltaic glass that maintains 
    natural lighting while generating clean electricity.
    """)
    
    # Apply yellow container styling
    st.markdown('<div class="yellow-container">', unsafe_allow_html=True)
    
    # Core BIPV Technology Explanation
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("""
        #### Revolutionary BIPV Glass Technology
        
        Our platform analyzes **semi-transparent photovoltaic glass** that replaces conventional windows 
        with advanced energy-generating materials:
        
        **🔬 Technology Specifications:**
        - **Efficiency Range:** 2-25% (basic to high-performance)
        - **Transparency:** 10-40% light transmission
        - **Aesthetics:** Seamless architectural integration
        - **Durability:** 25+ year lifespan with degradation <0.5%/year
        
        **🏗️ Application Areas:**
        - Educational buildings (classrooms, libraries, laboratories)
        - Commercial offices and retail spaces
        - Healthcare facilities and public buildings
        - Residential high-rise developments
        """)
    
    with col2:
        st.success("""
        **🎯 Platform Advantages:**
        
        ⚡ **Comprehensive Analysis**  
        11-step scientific workflow
        
        🤖 **AI-Powered Optimization**  
        Machine learning demand prediction
        
        🏢 **BIM Integration**  
        Revit model processing
        
        📊 **Financial Modeling**  
        NPV, IRR, payback analysis
        
        🌱 **Environmental Impact**  
        CO₂ savings quantification
        
        📈 **Performance Tracking**  
        25-year lifecycle assessment
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
    
    # Technology Innovation Section
    st.markdown("""
    ---
    
    ### 🚀 Technology Innovation & Industry Leadership
    
    Our platform incorporates the latest advances in BIPV technology, renewable energy optimization, 
    and sustainable building design:
    """)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        **🔬 Advanced Analytics:**
        - Multi-objective genetic algorithm optimization (NSGA-II)
        - Random Forest machine learning for demand prediction
        - ISO 15927-4 compliant TMY data generation
        - Real-time weather integration with OpenWeatherMap API
        - Comprehensive shading analysis and solar radiation modeling
        """)
    
    with col2:
        st.markdown("""
        **🌐 Industry Standards Compliance:**
        - ISO 15927-4: Climatic data for building design
        - ISO 9060: Solar radiation measurement standards
        - ASHRAE 90.1: Energy efficiency requirements
        - IEC 61853: Photovoltaic performance testing
        - EN 410: Glass thermal and optical properties
        """)
    
    # Enhanced Platform Capabilities
    st.markdown("""
    ---
    
    ### 🛠️ Comprehensive Platform Capabilities
    
    Our platform delivers end-to-end BIPV analysis through integrated tools and methodologies:
    """)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        **📊 Data Analytics:**
        - PostgreSQL database integration
        - Real-time performance tracking
        - Comprehensive report generation
        - CSV/HTML export capabilities
        - Multi-project management
        """)
    
    with col2:
        st.markdown("""
        **🔧 Engineering Tools:**
        - Genetic algorithm optimization
        - Multi-objective problem solving
        - Performance ratio calculations
        - Shading analysis algorithms
        - Grid integration modeling
        """)
    
    with col3:
        st.markdown("""
        **💰 Financial Modeling:**
        - NPV and IRR calculations
        - 25-year lifecycle analysis
        - Sensitivity analysis
        - ROI optimization
        - Carbon savings quantification
        """)
    
    # Success Stories and Applications
    st.markdown("""
    ---
    
    ### 🎯 Real-World Applications & Success Stories
    
    The BIPV Optimizer platform has been successfully applied across various educational and commercial projects:
    """)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        **🏫 Educational Buildings:**
        - **University libraries:** Large south-facing windows ideal for BIPV integration
        - **Classroom buildings:** Balanced energy generation and natural lighting
        - **Research facilities:** High-efficiency BIPV for energy-intensive operations
        - **Student dormitories:** Cost-effective BIPV solutions for residential applications
        """)
    
    with col2:
        st.markdown("""
        **🏢 Commercial Applications:**
        - **Office buildings:** Facade optimization for maximum energy yield
        - **Healthcare facilities:** Reliable energy generation for critical operations
        - **Retail spaces:** Aesthetic BIPV integration maintaining visual appeal
        - **Public buildings:** Sustainable energy solutions for government facilities
        """)
    
    # Getting Started Section
    st.markdown("""
    ---
    
    ### 🚀 Getting Started with BIPV Optimization
    
    Ready to transform your building into an energy producer? Follow these steps:
    """)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("""
        **Step-by-Step Process:**
        
        1. **📍 Project Setup:** Define location, timezone, and project parameters
        2. **📊 Data Upload:** Provide historical energy consumption data
        3. **🌤️ Weather Analysis:** Generate climate data for your location
        4. **🏗️ BIM Integration:** Upload building geometry and window data
        5. **☀️ Solar Analysis:** Calculate radiation and shading effects
        6. **🔋 System Design:** Specify BIPV technology and configurations
        7. **⚡ Energy Modeling:** Compare generation with demand patterns
        8. **🎯 Optimization:** Find optimal system configurations
        9. **💰 Financial Analysis:** Evaluate economic viability
        10. **📄 Reporting:** Generate comprehensive analysis reports
        11. **🤖 AI Consultation:** Get expert recommendations
        """)
    
    with col2:
        st.info("""
        **💡 Prerequisites:**
        
        ✅ **Building Data**  
        BIM model or window measurements
        
        ✅ **Energy History**  
        6-12 months consumption data
        
        ✅ **Project Goals**  
        Energy targets and budget
        
        ✅ **Technical Specs**  
        BIPV technology preferences
        
        **⏱️ Analysis Time:**  
        Complete workflow: 30-60 minutes
        """)
    
    # Technical Support and Documentation
    st.markdown("""
    ---
    
    ### 📚 Technical Support & Documentation
    
    Comprehensive resources available for successful BIPV implementation:
    """)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        **📖 Documentation:**
        - User manual and tutorials
        - API reference documentation
        - Best practices guide
        - Troubleshooting FAQ
        """)
    
    with col2:
        st.markdown("""
        **🔧 Technical Support:**
        - BIM integration assistance
        - Data format specifications
        - Performance optimization tips
        - System configuration guidance
        """)
    
    with col3:
        st.markdown("""
        **🎓 Training Resources:**
        - Video tutorials
        - Webinar series
        - Case study examples
        - Expert consultation
        """)
    
    # Call to Action
    st.markdown("""
    ---
    
    ### 🎯 Ready to Optimize Your Building?
    
    Transform your building into a sustainable energy producer with our comprehensive BIPV analysis platform.
    """)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.success("""
        **🚀 Start Your BIPV Journey Today!**
        
        Click "Next Step" below to begin with Project Setup and discover the energy generation 
        potential of your building through advanced BIPV glass integration.
        
        **Expected Outcomes:**
        - 30-80% energy demand coverage
        - 15-25 year payback period
        - Significant CO₂ emissions reduction
        - Enhanced building aesthetics
        - Increased property value
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
    
    # Section removed per user request
    

    
    # Research Attribution
    st.markdown("""
    ---
    
    ### Research Attribution
    
    **Developed by:** Mostafa Gabr  
    **Institution:** Technische Universität Berlin  
    **Research Focus:** Building-Integrated Photovoltaics Optimization  
    **Contact:** [ResearchGate Profile](https://www.researchgate.net/profile/Mostafa-Gabr-4)
    """)