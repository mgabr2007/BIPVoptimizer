"""
Dynamic Workflow Visualization Component
Provides visual step progression and completion tracking
"""

import streamlit as st
from database_manager import BIPVDatabaseManager
from services.io import get_current_project_id


def check_database_step_completion(project_id, step_key):
    """Check if a step is completed by querying the database"""
    if not project_id:
        return False
    
    db_manager = BIPVDatabaseManager()
    conn = db_manager.get_connection()
    if not conn:
        return False
    
    try:
        with conn.cursor() as cursor:
            # Map step keys to database tables
            step_table_mapping = {
                'project_setup': 'projects',
                'historical_data': 'ai_models',  # Historical data creates AI models
                'weather_environment': 'weather_data',
                'facade_extraction': 'building_elements',
                'radiation_grid': 'element_radiation',
                'pv_specification': 'pv_specifications',
                'yield_demand': 'energy_analysis',
                'optimization': 'optimization_results',
                'financial_analysis': 'financial_analysis',
                'reporting': 'comprehensive_reports',
                'ai_consultation': 'ai_consultation_results'
            }
            
            table_name = step_table_mapping.get(step_key)
            if not table_name:
                return False
            
            # Check if there's data in the corresponding table
            cursor.execute(f"SELECT COUNT(*) FROM {table_name} WHERE project_id = %s", (project_id,))
            result = cursor.fetchone()
            return result[0] > 0 if result else False
            
    except Exception as e:
        # Handle tables that might not exist yet
        return False
    finally:
        conn.close()


def render_workflow_progress(workflow_steps, current_step):
    """Render dynamic workflow visualization with progress tracking"""
    
    # Find current step index
    current_index = next((i for i, (key, _, _) in enumerate(workflow_steps) if key == current_step), 0)
    
    # Get current project ID for database checking
    project_id = get_current_project_id()
    
    # Calculate completion status for each step using database
    completion_status = []
    for i, (step_key, step_name, description) in enumerate(workflow_steps):
        # Check database completion status
        is_completed_in_db = check_database_step_completion(project_id, step_key)
        
        if step_key == current_step:
            status = "current"
        elif is_completed_in_db:
            status = "completed"
        else:
            status = "pending"
        
        completion_status.append({
            'step': i + 1,
            'key': step_key,
            'name': step_name,
            'description': description,
            'status': status
        })
    
    # Create visual progress bar
    st.markdown("### 🔄 Workflow Progress")
    
    # Calculate progress based on completed steps, not just current position
    completed_steps = sum(1 for step in completion_status if step['status'] == 'completed')
    progress_percentage = (completed_steps / len(workflow_steps)) * 100
    st.progress(progress_percentage / 100)
    st.caption(f"Progress: {progress_percentage:.0f}% ({completed_steps}/{len(workflow_steps)} steps)")
    
    # Visual step indicators
    st.markdown("---")
    
    # Create columns for step visualization
    cols = st.columns(len(workflow_steps))
    
    for i, step_info in enumerate(completion_status):
        with cols[i]:
            # Step icon based on status
            if step_info['status'] == 'completed':
                icon = "✅"
                color = "#28a745"  # Green
            elif step_info['status'] == 'current':
                icon = "🔄"
                color = "#007bff"  # Blue
            else:
                icon = "⏳"
                color = "#6c757d"  # Gray
            
            # Step display
            st.markdown(f"""
            <div style="text-align: center; padding: 10px;">
                <div style="font-size: 24px; color: {color};">{icon}</div>
                <div style="font-size: 12px; font-weight: bold; margin-top: 5px;">
                    Step {step_info['step']}
                </div>
                <div style="font-size: 10px; color: #666;">
                    {step_info['name'].replace('🏠 ', '').replace('1️⃣ ', '').replace('2️⃣ ', '').replace('3️⃣ ', '').replace('4️⃣ ', '').replace('5️⃣ ', '').replace('6️⃣ ', '').replace('7️⃣ ', '').replace('8️⃣ ', '').replace('9️⃣ ', '').replace('🔟 ', '')}
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    # Current step details
    st.markdown("---")
    current_step_info = completion_status[current_index]
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col1:
        if current_index > 0:
            prev_step = completion_status[current_index - 1]
            st.markdown(f"""
            **Previous:**  
            ✅ {prev_step['name']}
            """)
    
    with col2:
        st.markdown(f"""
        <div style="text-align: center; padding: 15px; border: 2px solid #007bff; border-radius: 10px; background-color: #f8f9fa;">
            <h4 style="margin: 0; color: #007bff;">🔄 Current Step</h4>
            <h3 style="margin: 5px 0; color: #333;">{current_step_info['name']}</h3>
            <p style="margin: 0; color: #666; font-size: 14px;">{current_step_info['description']}</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        if current_index < len(workflow_steps) - 1:
            next_step = completion_status[current_index + 1]
            st.markdown(f"""
            **Next:**  
            ⏳ {next_step['name']}
            """)
    
    return completion_status


def render_compact_progress(workflow_steps, current_step):
    """Render compact progress indicator for sidebar or header"""
    
    current_index = next((i for i, (key, _, _) in enumerate(workflow_steps) if key == current_step), 0)
    progress_percentage = (current_index / len(workflow_steps)) * 100
    
    # Compact progress bar
    st.markdown(f"""
    <div style="margin: 10px 0;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 5px;">
            <span style="font-size: 12px; font-weight: bold;">Workflow Progress</span>
            <span style="font-size: 12px; color: #666;">{current_index + 1}/{len(workflow_steps)}</span>
        </div>
        <div style="width: 100%; background-color: #e0e0e0; border-radius: 10px; height: 8px;">
            <div style="width: {progress_percentage}%; background-color: #007bff; border-radius: 10px; height: 8px;"></div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_step_completion_tracker():
    """Render completion tracker based on session state"""
    
    completion_flags = {
        'setup_completed': 'Project Setup',
        'historical_completed': 'Historical Data',
        'weather_completed': 'Weather Integration',
        'building_elements_completed': 'BIM Extraction',
        'radiation_completed': 'Radiation Analysis',
        'pv_specs_completed': 'PV Specification',
        'yield_demand_completed': 'Yield vs Demand',
        'optimization_completed': 'Optimization',
        'financial_completed': 'Financial Analysis'
    }
    
    st.markdown("### ✅ Completed Steps")
    
    completed_count = 0
    total_count = len(completion_flags)
    
    for flag, step_name in completion_flags.items():
        is_completed = st.session_state.get(flag, False)
        if is_completed:
            completed_count += 1
            st.markdown(f"✅ {step_name}")
        else:
            st.markdown(f"⏳ {step_name}")
    
    # Completion percentage
    completion_percentage = (completed_count / total_count) * 100
    st.metric("Overall Completion", f"{completion_percentage:.0f}%")
    
    return completed_count, total_count


def render_workflow_navigation_enhanced(workflow_steps, current_step):
    """Enhanced navigation with visual feedback"""
    
    current_index = next((i for i, (key, _, _) in enumerate(workflow_steps) if key == current_step), 0)
    project_id = get_current_project_id()
    
    st.markdown("### 🗺️ Workflow Navigation")
    
    # Create navigation grid
    cols = st.columns(3)
    
    for i, (step_key, step_name, description) in enumerate(workflow_steps):
        col_idx = i % 3
        
        with cols[col_idx]:
            is_current = (step_key == current_step)
            is_completed = check_database_step_completion(project_id, step_key)
            
            # Button styling based on status
            if is_current:
                button_type = "primary"
                prefix = "🔄 "
            elif is_completed:
                button_type = "secondary"
                prefix = "✅ "
            else:
                button_type = "secondary"
                prefix = "⏳ "
            
            # Navigation button
            if st.button(
                f"{prefix}{step_name}",
                key=f"nav_enhanced_{step_key}_{i}",
                help=description,
                type=button_type,
                use_container_width=True,
                disabled=is_current
            ):
                st.session_state.current_step = step_key
                st.session_state.scroll_to_top = True
                st.rerun()
            
            # Step description
            st.caption(description)
    
    return current_index


def render_milestone_tracker():
    """Track and display major milestones in the workflow"""
    
    milestones = [
        {
            'name': 'Project Foundation',
            'steps': ['welcome', 'project_setup', 'historical_data'],
            'description': 'Basic project setup and data collection'
        },
        {
            'name': 'Analysis Phase',
            'steps': ['weather_environment', 'facade_extraction', 'radiation_grid'],
            'description': 'Technical analysis and modeling'
        },
        {
            'name': 'Design Phase',
            'steps': ['pv_specification', 'yield_demand'],
            'description': 'System design and performance calculation'
        },
        {
            'name': 'Optimization Phase',
            'steps': ['optimization', 'financial_analysis'],
            'description': 'Multi-objective optimization and economic analysis'
        },
        {
            'name': 'Completion Phase',
            'steps': ['reporting'],
            'description': 'Report generation and project finalization'
        }
    ]
    
    current_step = st.session_state.get('current_step', 'welcome')
    
    st.markdown("### 🎯 Project Milestones")
    
    for milestone in milestones:
        # Check milestone completion
        total_steps = len(milestone['steps'])
        is_current_milestone = current_step in milestone['steps']
        
        if is_current_milestone:
            current_step_index = milestone['steps'].index(current_step)
            completed_steps = current_step_index
            is_completed_milestone = False
        else:
            # Check if all steps in this milestone come before current step
            try:
                workflow_order = ['welcome', 'project_setup', 'historical_data', 'weather_environment', 
                                'facade_extraction', 'radiation_grid', 'pv_specification', 'yield_demand', 
                                'optimization', 'financial_analysis', 'reporting']
                current_order = workflow_order.index(current_step)
                milestone_max_order = max(workflow_order.index(step) for step in milestone['steps'])
                is_completed_milestone = milestone_max_order < current_order
                completed_steps = total_steps if is_completed_milestone else 0
            except (ValueError, IndexError):
                is_completed_milestone = False
                completed_steps = 0
        
        # Milestone status
        if is_completed_milestone:
            status_icon = "✅"
            status_color = "#28a745"
        elif is_current_milestone:
            status_icon = "🔄"
            status_color = "#007bff"
        else:
            status_icon = "⏳"
            status_color = "#6c757d"
        
        # Display milestone
        with st.expander(f"{status_icon} {milestone['name']}", expanded=is_current_milestone):
            st.markdown(f"*{milestone['description']}*")
            
            # Progress within milestone
            if is_current_milestone:
                current_step_in_milestone = milestone['steps'].index(current_step)
                milestone_progress = (current_step_in_milestone / total_steps) * 100
                st.progress(milestone_progress / 100)
                st.caption(f"Progress: {milestone_progress:.0f}% ({current_step_in_milestone + 1}/{total_steps} steps)")
            
            # List steps in milestone
            for step in milestone['steps']:
                step_display_name = step.replace('_', ' ').title()
                
                if step == current_step:
                    st.markdown(f"🔄 **{step_display_name}** (Current)")
                elif is_current_milestone and milestone['steps'].index(step) < milestone['steps'].index(current_step):
                    st.markdown(f"✅ {step_display_name}")
                elif is_completed_milestone:
                    st.markdown(f"✅ {step_display_name}")
                else:
                    st.markdown(f"⏳ {step_display_name}")