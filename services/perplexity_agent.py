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
            "model": "llama-3.1-sonar-small-128k-online",
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
            response.raise_for_status()
            
            result = response.json()
            return result['choices'][0]['message']['content']
            
        except requests.exceptions.RequestException as e:
            return f"Error connecting to Perplexity API: {str(e)}"
        except (KeyError, IndexError) as e:
            return f"Error parsing API response: {str(e)}"
        except Exception as e:
            return f"Unexpected error: {str(e)}"


def render_perplexity_consultation():
    """Render Perplexity AI consultation interface"""
    
    # Add OptiSunny character header image
    st.image("attached_assets/step11_1751436847832.png", width=400)
    
    st.header("🤖 AI Research Consultation")
    st.write("Get expert analysis and optimization recommendations from Perplexity AI")
    
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
    
    # Initialize agent with API key
    import os
    api_key = os.getenv("PERPLEXITY_API_KEY", "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")
    agent = PerplexityBIPVAgent(api_key)
    
    # Get project data
    project_data = st.session_state.get('project_data', {})
    project_name = project_data.get('project_name', 'Current Project')
    
    # Load comprehensive data from database
    db_data = get_project_report_data(project_name)
    if not db_data:
        st.warning("No project data found. Please complete the workflow analysis first.")
        return
    
    # Use database data as primary source, fallback to session state
    building_elements = db_data.get('building_elements', [])
    financial_analysis = db_data.get('financial_analysis', project_data.get('financial_analysis', {}))
    
    # Merge all available data for comprehensive analysis
    comprehensive_project_data = {
        **project_data,
        **db_data,
        'building_elements': building_elements,
        'financial_analysis': financial_analysis
    }
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔍 Analyze Complete Results", type="primary"):
            with st.spinner("Consulting AI research expert..."):
                analysis = agent.analyze_bipv_results(comprehensive_project_data, building_elements, financial_analysis)
                st.session_state.perplexity_analysis = analysis
    
    with col2:
        if st.button("💡 Get Optimization Tips"):
            # Identify low performance areas
            low_performance = []
            
            # Check AI model performance
            r_squared = project_data.get('historical_data', {}).get('r_squared', 0)
            if r_squared < 0.85:
                low_performance.append(f"AI model R² score: {r_squared:.3f} (needs improvement)")
            
            # Check economic viability
            financial_metrics = financial_analysis.get('financial_metrics', {})
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
    - Recommendations tailored to your specific project data
    - Focuses on improving calculation accuracy and system performance
    - References current publications and best practices (2023-2025)
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