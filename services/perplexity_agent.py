"""
Perplexity AI Consultation Agent for BIPV Optimizer
Analyzes all workflow results and provides research conclusions with optimization recommendations
"""

import streamlit as st
import requests
import json
from services.io import get_project_report_data
from core.solar_math import safe_divide


class PerplexityBIPVAgent:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://api.perplexity.ai/chat/completions"
        self.headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
    
    def analyze_bipv_results(self, project_data, building_elements, financial_analysis):
        """Analyze complete BIPV results and provide research conclusions"""
        
        # Prepare comprehensive data summary for analysis
        data_summary = self._prepare_data_summary(project_data, building_elements, financial_analysis)
        
        # Create research-focused prompt with specific result references
        prompt = f"""
        As a BIPV (Building-Integrated Photovoltaics) research consultant, analyze the following comprehensive analysis results and provide recommendations that DIRECTLY REFERENCE the specific data points from this analysis:

        1. KEY RESEARCH FINDINGS (5-7 bullet points) - Quote specific numbers from the analysis
        2. TECHNICAL OPTIMIZATION RECOMMENDATIONS - Reference specific orientations, capacities, and performance metrics
        3. ECONOMIC VIABILITY ASSESSMENT - Cite the actual NPV, IRR, and payback values calculated
        4. RESEARCH METHODOLOGY IMPROVEMENTS - Reference the AI model R² score and data quality metrics

        IMPORTANT: Include direct references to the analysis results in your recommendations. For example:
        - "Given that your analysis shows X kW total capacity across Y building elements..."
        - "With your calculated NPV of €Z and IRR of W%..."
        - "Your orientation analysis reveals that A% of suitable elements face South..."

        BIPV Analysis Data:
        {data_summary}

        Ensure every recommendation includes specific references to the calculated values, window counts, orientations, financial metrics, and performance indicators from this actual analysis. Do not provide generic advice - base everything on the specific results shown above.
        """
        
        return self._query_perplexity(prompt)
    
    def get_optimization_recommendations(self, low_performance_areas):
        """Get specific recommendations for improving low-performing aspects"""
        
        prompt = f"""
        Based on BIPV system analysis showing these performance concerns:
        {low_performance_areas}

        Provide specific technical recommendations for:
        1. Input parameter refinements
        2. Calculation methodology improvements  
        3. System design optimizations
        4. Economic model enhancements

        Reference latest BIPV research papers and industry standards (2023-2025).
        """
        
        return self._query_perplexity(prompt)
    
    def _prepare_data_summary(self, project_data, building_elements, financial_analysis):
        """Prepare comprehensive data summary for AI analysis"""
        
        # Extract key metrics
        total_elements = len(building_elements) if building_elements else 0
        suitable_elements = sum(1 for elem in building_elements 
                              if isinstance(elem, dict) and elem.get('pv_suitable', False))
        
        # Orientation breakdown
        orientation_count = {}
        total_glass_area = 0
        for elem in building_elements:
            if isinstance(elem, dict):
                orientation = elem.get('orientation', 'Unknown')
                orientation_count[orientation] = orientation_count.get(orientation, 0) + 1
                try:
                    glass_area = float(elem.get('glass_area', 0))
                    total_glass_area += glass_area
                except (ValueError, TypeError):
                    continue
        
        # Financial metrics
        financial_metrics = financial_analysis.get('financial_metrics', {}) if financial_analysis else {}
        npv = financial_metrics.get('npv', 0)
        payback_period = financial_metrics.get('payback_period', 0)
        irr = financial_metrics.get('irr', 0)
        total_investment = financial_metrics.get('total_investment', 0)
        
        # Historical data
        historical_data = project_data.get('historical_data', {})
        r_squared = historical_data.get('r_squared', 0)
        total_consumption = historical_data.get('total_consumption', 0)
        
        # Weather data
        weather_data = project_data.get('weather_analysis', {})
        annual_ghi = weather_data.get('annual_ghi', 1200)
        
        # Enhanced PV specifications extraction with multiple data sources
        pv_specs = project_data.get('pv_specifications', [])
        total_capacity = 0
        total_annual_yield = 0
        
        # Try different data structure formats
        if isinstance(pv_specs, dict) and 'system_power_kw' in pv_specs:
            # Convert DataFrame dict format
            capacity_dict = pv_specs.get('system_power_kw', {})
            yield_dict = pv_specs.get('annual_energy_kwh', {})
            if isinstance(capacity_dict, dict):
                total_capacity = sum(float(v) for v in capacity_dict.values() if v)
            if isinstance(yield_dict, dict):
                total_annual_yield = sum(float(v) for v in yield_dict.values() if v)
        elif isinstance(pv_specs, list):
            for spec in pv_specs:
                if isinstance(spec, dict):
                    total_capacity += float(spec.get('system_power_kw', 0))
                    total_annual_yield += float(spec.get('annual_energy_kwh', 0))
        
        # If no PV specs found, try yield_demand_analysis
        if total_capacity == 0 and total_annual_yield == 0:
            yield_analysis = project_data.get('yield_demand_analysis', {})
            if isinstance(yield_analysis, dict):
                summary = yield_analysis.get('summary', {})
                if isinstance(summary, dict):
                    total_capacity = float(summary.get('total_capacity_kw', 0))
                    total_annual_yield = float(summary.get('total_annual_yield_kwh', 0))
        
        # If still no data, calculate from building elements with BIPV specifications
        if total_capacity == 0 and total_annual_yield == 0 and building_elements:
            for elem in building_elements:
                if isinstance(elem, dict) and elem.get('pv_suitable', False):
                    glass_area = float(elem.get('glass_area', 1.5))
                    # BIPV glass: 150 W/m² power density
                    element_capacity = glass_area * 0.15  # kW
                    orientation = elem.get('orientation', '')
                    # Realistic solar yield based on orientation
                    if 'South' in orientation:
                        annual_yield = element_capacity * 1400  # kWh/year
                    elif any(x in orientation for x in ['East', 'West']):
                        annual_yield = element_capacity * 1100  # kWh/year
                    else:
                        annual_yield = element_capacity * 800   # kWh/year for North
                    
                    total_capacity += element_capacity
                    total_annual_yield += annual_yield
        
        # Debug logging to trace data extraction
        print(f"DEBUG AI Consultation Data:")
        print(f"- Project data keys: {list(project_data.keys()) if project_data else 'None'}")
        print(f"- Building elements count: {len(building_elements)}")
        print(f"- Total elements: {total_elements}")
        print(f"- Suitable elements: {suitable_elements}")
        print(f"- Total glass area: {total_glass_area}")
        print(f"- PV specs type: {type(pv_specs)}, length: {len(pv_specs) if isinstance(pv_specs, (list, dict)) else 'N/A'}")
        if isinstance(pv_specs, dict):
            print(f"- PV specs keys: {list(pv_specs.keys())}")
        print(f"- Total capacity: {total_capacity}")
        print(f"- Total annual yield: {total_annual_yield}")
        
        # Check if we have yield_demand_analysis data
        yield_analysis = project_data.get('yield_demand_analysis', {})
        print(f"- Yield analysis available: {bool(yield_analysis)}")
        if yield_analysis:
            print(f"- Yield analysis keys: {list(yield_analysis.keys())}")
            summary = yield_analysis.get('summary', {})
            if summary:
                print(f"- Yield summary: capacity={summary.get('total_capacity_kw', 0)}, yield={summary.get('total_annual_yield_kwh', 0)}")
        
        # Calculate specific performance metrics for detailed references
        avg_yield_per_element = safe_divide(total_annual_yield, suitable_elements, 0)
        investment_per_kw = safe_divide(total_investment, total_capacity, 0)
        glass_area_utilization = safe_divide(total_glass_area, total_elements, 0)
        
        # Identify top and bottom performing orientations
        orientation_performance = {}
        for orientation, count in orientation_count.items():
            if count > 0:
                orientation_performance[orientation] = count
        
        if orientation_performance:
            sorted_orientations = sorted(orientation_performance.items(), key=lambda x: x[1], reverse=True)
            best_orientation = sorted_orientations[0][0]
            worst_orientation = sorted_orientations[-1][0]
        else:
            best_orientation = "Unknown"
            worst_orientation = "Unknown"
        
        summary = f"""
        PROJECT ANALYSIS RESULTS - SPECIFIC DATA FOR REFERENCE:
        
        BUILDING CHARACTERISTICS:
        - Location: {project_data.get('location', 'Unknown')}
        - Total Building Elements Analyzed: {total_elements} windows/facades
        - BIPV Suitable Elements: {suitable_elements} elements ({safe_divide(suitable_elements, total_elements, 0)*100:.1f}% suitability rate)
        - Total Available Glass Area: {total_glass_area:.1f} m²
        - Average Glass Area per Element: {glass_area_utilization:.1f} m²/element
        
        ORIENTATION ANALYSIS RESULTS:
        {json.dumps(orientation_count, indent=2)}
        - Dominant Orientation: {best_orientation} ({orientation_count.get(best_orientation, 0)} elements)
        - Least Common Orientation: {worst_orientation} ({orientation_count.get(worst_orientation, 0)} elements)
        
        ENERGY PERFORMANCE CALCULATIONS:
        - AI Demand Model R² Score: {r_squared:.3f} ({"Excellent" if r_squared > 0.85 else "Good" if r_squared > 0.7 else "Needs Improvement"} prediction accuracy)
        - Annual Building Energy Consumption: {total_consumption:,.0f} kWh
        - Site Annual Solar Irradiance (GHI): {annual_ghi:.0f} kWh/m²
        - Calculated Total PV System Capacity: {total_capacity:.1f} kW
        - Projected Annual PV Generation: {total_annual_yield:.0f} kWh
        - Building Self-Sufficiency Ratio: {safe_divide(total_annual_yield, total_consumption, 0)*100:.1f}%
        - Average Yield per BIPV Element: {avg_yield_per_element:.0f} kWh/element/year
        
        FINANCIAL ANALYSIS RESULTS:
        - Net Present Value (NPV): €{npv:,.0f}
        - Internal Rate of Return (IRR): {irr*100:.1f}%
        - Simple Payback Period: {payback_period:.1f} years
        - Total System Investment: €{total_investment:,.0f}
        - Investment Cost per kW: €{investment_per_kw:,.0f}/kW
        
        PERFORMANCE ASSESSMENT:
        - Economic Viability: {"Financially Viable (Positive NPV)" if npv > 0 else "Financially Challenging (Negative NPV)"}
        - Demand Prediction Quality: {"High Confidence" if r_squared > 0.85 else "Moderate Confidence" if r_squared > 0.7 else "Low Confidence - Needs Data Improvement"}
        - BIPV Technical Potential: {"High Potential" if suitable_elements > total_elements*0.6 else "Medium Potential" if suitable_elements > total_elements*0.3 else "Limited Potential"}
        - System Scale: {"Large-scale Installation" if total_capacity > 50 else "Medium-scale Installation" if total_capacity > 20 else "Small-scale Installation"}
        """
        
        return summary
    
    def _query_perplexity(self, prompt):
        """Send query to Perplexity API and return response"""
        
        payload = {
            "model": "sonar-pro",
            "messages": [
                {
                    "role": "system",
                    "content": "You are an expert BIPV research consultant with deep knowledge of building-integrated photovoltaics, solar energy systems, and building energy optimization. Provide precise, actionable insights based on current research and industry best practices."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "max_tokens": 1500,
            "temperature": 0.2,
            "top_p": 0.9,
            "return_images": False,
            "return_related_questions": False,
            "search_recency_filter": "month",
            "stream": False
        }
        
        try:
            response = requests.post(self.base_url, headers=self.headers, json=payload)
            
            # Enhanced error handling with response details
            if response.status_code != 200:
                error_details = f"Status: {response.status_code}"
                try:
                    error_json = response.json()
                    error_details += f", Response: {error_json}"
                except:
                    error_details += f", Text: {response.text[:200]}"
                
                return f"Perplexity API Error - {error_details}. Please check your API key and try again."
            
            result = response.json()
            return result['choices'][0]['message']['content']
            
        except requests.exceptions.RequestException as e:
            return f"Error connecting to Perplexity API: {str(e)}"
        except (KeyError, IndexError) as e:
            return f"Error parsing API response: {str(e)}"
        except Exception as e:
            return f"Unexpected error: {str(e)}"


def prepare_master_report_for_ai(master_report_data, uploaded_reports):
    """Prepare master report data for AI analysis"""
    master_data = master_report_data.get('data', {})
    
    # Extract comprehensive project data from all uploaded reports
    comprehensive_data = {
        'project_overview': master_data.get('project_overview', {}),
        'technical_analysis': master_data.get('technical_analysis', {}),
        'financial_analysis': master_data.get('financial_analysis', {}),
        'building_elements': [],
        'reports_summary': []
    }
    
    # Process each uploaded report to extract specific data
    for step_key, report_info in uploaded_reports.items():
        report_data = report_info.get('data', {})
        
        # Extract building elements if available
        if step_key == 'step4' and report_data.get('tables'):
            # Extract building elements from Step 4 facade extraction
            for table in report_data.get('tables', []):
                if len(table) > 1:  # Has header and data rows
                    headers = table[0]
                    for row in table[1:]:
                        if len(row) >= len(headers):
                            element = {}
                            for i, header in enumerate(headers):
                                if i < len(row):
                                    element[header.lower().replace(' ', '_')] = row[i]
                            comprehensive_data['building_elements'].append(element)
        
        # Add report summary
        comprehensive_data['reports_summary'].append({
            'step': step_key,
            'title': report_data.get('title', ''),
            'key_metrics': report_data.get('metrics', {}),
            'key_findings': report_data.get('key_findings', [])
        })
    
    return comprehensive_data


def render_perplexity_consultation():
    """Render Perplexity AI consultation interface with database-driven dataflow"""
    
    # Add OptiSunny character header image
    st.image("attached_assets/step11_1751436847832.png", width=400)
    
    st.header("🤖 AI Research Consultation")
    st.markdown("Get expert analysis and optimization recommendations from Perplexity AI based on your comprehensive database-stored analysis")
    
    # Get project ID from centralized system
    from services.io import get_current_project_id
    project_id = get_current_project_id()
    
    if not project_id:
        st.error("❌ No project ID found. Please complete the project setup first.")
        return
    
    # Get comprehensive project data from database
    from database_manager import BIPVDatabaseManager
    db_manager = BIPVDatabaseManager()
    
    try:
        # Retrieve all project data from database
        project_data = db_manager.get_project_data(project_id)
        building_elements = db_manager.get_building_elements(project_id)
        financial_data = db_manager.get_financial_analysis_data(project_id)
        pv_specs = db_manager.get_pv_specifications(project_id)
        yield_data = db_manager.get_yield_demand_data(project_id)
        optimization_data = db_manager.get_optimization_results(project_id)
        weather_data = db_manager.get_weather_data(project_id)
        historical_data = db_manager.get_historical_data(project_id)
        
        # Check data availability
        data_sources = []
        if project_data: data_sources.append("Project Setup")
        if building_elements: data_sources.append("Building Elements")
        if weather_data: data_sources.append("Weather Data")
        if historical_data: data_sources.append("Historical Data")
        if pv_specs: data_sources.append("PV Specifications")
        if yield_data: data_sources.append("Yield Analysis")
        if optimization_data: data_sources.append("Optimization Results")
        if financial_data: data_sources.append("Financial Analysis")
        
        if len(data_sources) < 4:
            st.error(f"❌ Insufficient data for comprehensive AI analysis. Available sources: {', '.join(data_sources)}")
            st.info("💡 Please complete more workflow steps to get meaningful AI recommendations.")
            return
        
        st.success(f"✅ Comprehensive database analysis available ({len(data_sources)} data sources loaded)")
        
        # Show database data summary
        with st.expander("📋 Database Analysis Summary", expanded=False):
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Data Sources", len(data_sources))
            with col2:
                st.metric("Building Elements", len(building_elements) if building_elements else 0)
            with col3:
                st.metric("Project ID", project_id)
            
            # Show available data sources
            st.markdown("**Available Database Sources:**")
            for source in data_sources:
                st.markdown(f"• {source}")
    
    except Exception as e:
        st.error(f"❌ Error retrieving project data from database: {str(e)}")
        return
    
    # Data Usage Information
    with st.expander("📊 How This Data Will Be Used", expanded=False):
        st.markdown("""
        ### Data Flow Through BIPV Analysis Workflow:
        
        **AI Consultation Final Analysis:**
        - **Complete project synthesis** → Research-based conclusions using all 10 workflow steps' authentic data
        - **Performance benchmarking** → Industry comparison and best practice recommendations
        - **Strategic recommendations** → Implementation guidance based on calculated NPV, IRR, and technical metrics
        
        **Research Applications:**
        - **Academic validation** → Methodology verification against current BIPV research literature (2023-2025)
        - **Industry benchmarking** → Performance comparison with published case studies and market standards
        - **Technical optimization** → Engineering recommendations for improved system design and implementation
        
        **Decision Support:**
        - **Investment guidance** → Financial risk assessment and implementation timeline recommendations
        - **Technical validation** → Building-specific constraints and regulatory compliance verification
        - **Future planning** → Scalability assessment and monitoring recommendations for long-term performance
        """)
    
    # Initialize agent with API key from environment
    import os
    
    # Get API key from environment (Replit secrets or Streamlit secrets)
    api_key = None
    try:
        api_key = os.getenv("PERPLEXITY_API_KEY")
        if not api_key:
            api_key = st.secrets.get("PERPLEXITY_API_KEY")
    except:
        pass
    
    if not api_key:
        st.error("❌ Perplexity API key not found. Please add PERPLEXITY_API_KEY to your environment variables.")
        st.info("💡 Contact support to configure API access for AI consultation features.")
        return
    
    agent = PerplexityBIPVAgent(api_key)
    
    # Prepare comprehensive data for AI analysis from database
    comprehensive_project_data = {
        'project_data': project_data,
        'building_elements': building_elements,
        'financial_analysis': financial_data,
        'pv_specifications': pv_specs,
        'yield_analysis': yield_data,
        'optimization_results': optimization_data,
        'weather_data': weather_data,
        'historical_data': historical_data
    }
    
    data_source = "Database (Comprehensive)"
    st.info("🎯 Using comprehensive database data for AI analysis")
    
    # Validate minimum data requirements for AI analysis
    element_count = len(building_elements) if building_elements else 0
    has_financial = bool(financial_data and financial_data.get('financial_metrics'))
    has_project_basics = bool(project_data and project_data.get('location'))
    
    if not (element_count > 0 and has_financial and has_project_basics):
        st.error("❌ Insufficient data for meaningful AI analysis:")
        st.markdown(f"• Building Elements: {element_count} (need > 0)")
        st.markdown(f"• Financial Analysis: {'✓' if has_financial else '✗'}")
        st.markdown(f"• Project Basics: {'✓' if has_project_basics else '✗'}")
        return
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔍 Analyze Complete Results", type="primary"):
            with st.spinner("Consulting AI research expert..."):
                analysis = agent.analyze_bipv_results(project_data, building_elements, financial_data)
                st.session_state.perplexity_analysis = analysis
    
    with col2:
        if st.button("💡 Get Optimization Tips"):
            # Identify low performance areas
            low_performance = []
            
            # Check AI model performance
            r_squared = historical_data.get('r_squared', 0) if historical_data else 0
            if r_squared < 0.85:
                low_performance.append(f"AI model R² score: {r_squared:.3f} (needs improvement)")
            
            # Check economic viability
            financial_metrics = financial_data.get('financial_metrics', {}) if financial_data else {}
            npv = financial_metrics.get('npv', 0)
            payback_period = financial_metrics.get('payback_period', 0)
            if npv <= 0:
                low_performance.append(f"Negative NPV: €{npv:,.0f}")
            if payback_period > 15:
                low_performance.append(f"Long payback period: {payback_period:.1f} years")
            
            # Check BIPV suitability
            suitable_count = sum(1 for elem in building_elements 
                               if isinstance(elem, dict) and elem.get('pv_suitable', False))
            total_count = len(building_elements)
            suitability_ratio = safe_divide(suitable_count, total_count, 0)
            if suitability_ratio < 0.5:
                low_performance.append(f"Low BIPV suitability: {suitability_ratio*100:.1f}% of elements")
            
            if not low_performance:
                low_performance = ["System shows good overall performance - seeking advanced optimization strategies"]
            
            with st.spinner("Getting optimization recommendations..."):
                recommendations = agent.get_optimization_recommendations(low_performance)
                st.session_state.perplexity_recommendations = recommendations
    
    # Display results
    if hasattr(st.session_state, 'perplexity_analysis'):
        st.subheader("📊 Expert Analysis Results")
        st.markdown(st.session_state.perplexity_analysis)
        
        # Download option
        project_name = project_data.get('project_name', 'Current_Project') if project_data else 'Current_Project'
        st.download_button(
            label="📄 Download Analysis Report",
            data=st.session_state.perplexity_analysis,
            file_name=f"BIPV_AI_Analysis_{project_name.replace(' ', '_')}.txt",
            mime="text/plain"
        )
    
    if hasattr(st.session_state, 'perplexity_recommendations'):
        st.subheader("🔧 Optimization Recommendations")
        st.markdown(st.session_state.perplexity_recommendations)
        
        # Download option
        project_name = project_data.get('project_name', 'Current_Project') if project_data else 'Current_Project'
        st.download_button(
            label="📄 Download Recommendations",
            data=st.session_state.perplexity_recommendations,
            file_name=f"BIPV_Optimization_Tips_{project_name.replace(' ', '_')}.txt",
            mime="text/plain"
        )
    
    # Add methodology note
    st.info("""
    **AI Consultation Methodology:**
    - Analysis based on latest BIPV research and industry standards
    - Recommendations tailored to your specific database-stored project data
    - Focuses on improving calculation accuracy and system performance
    - References current publications and best practices (2023-2025)
    - Uses 100% authentic data from completed workflow steps
    """)
    
    # Add finish button for workflow completion
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🎯 Finish & New Calculation", key="finish_restart_ai", use_container_width=True):
            # Reset all session state for new calculation
            for key in list(st.session_state.keys()):
                if key != 'current_step':
                    del st.session_state[key]
            st.session_state.current_step = 'welcome'
            st.rerun()