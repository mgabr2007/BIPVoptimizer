"""
BIPV Optimizer UI Standards Module
Provides consistent UI components and patterns across all workflow steps
"""

import streamlit as st
from utils.color_schemes import YELLOW_SCHEME, YELLOW_EMOJIS

# Step configuration with consistent naming and emojis
WORKFLOW_STEPS = {
    'welcome': {'number': 0, 'emoji': '🏠', 'title': 'Welcome', 'key': 'welcome'},
    'project_setup': {'number': 1, 'emoji': '🏢', 'title': 'Project Setup', 'key': 'project_setup'},
    'historical_data': {'number': 2, 'emoji': '📊', 'title': 'Historical Data & AI Training', 'key': 'historical_data'},
    'weather_environment': {'number': 3, 'emoji': '🌤️', 'title': 'Weather & Environment', 'key': 'weather_environment'},
    'facade_extraction': {'number': 4, 'emoji': '🏗️', 'title': 'BIM Data & Window Selection', 'key': 'facade_extraction'},
    'radiation_analysis': {'number': 5, 'emoji': '☀️', 'title': 'Solar Radiation Analysis', 'key': 'radiation_grid'},
    'pv_specification': {'number': 6, 'emoji': '⚡', 'title': 'BIPV Glass Specification', 'key': 'pv_specification_unified'},
    'yield_demand': {'number': 7, 'emoji': '⚖️', 'title': 'Energy Yield vs Demand', 'key': 'yield_demand'},
    'optimization': {'number': 8, 'emoji': '🎯', 'title': 'Multi-Objective Optimization', 'key': 'optimization'},
    'financial_analysis': {'number': 9, 'emoji': '💰', 'title': 'Financial & Environmental Analysis', 'key': 'financial_analysis'},
    'comprehensive_dashboard': {'number': 10, 'emoji': '📈', 'title': 'Comprehensive Dashboard', 'key': 'comprehensive_dashboard'},
    'ai_consultation': {'number': 11, 'emoji': '🤖', 'title': 'AI Research Consultation', 'key': 'perplexity_agent'}
}

def render_step_header(step_key, subtitle=None):
    """Render consistent step header with emoji and title"""
    step = WORKFLOW_STEPS.get(step_key)
    if not step:
        return
    
    if step['number'] == 0:
        # Welcome page - no step number
        st.title(f"{step['emoji']} {step['title']}")
    else:
        st.title(f"{step['emoji']} Step {step['number']}: {step['title']}")
    
    if subtitle:
        st.markdown(f"*{subtitle}*")
    
    st.markdown("---")

def render_section_header(title, emoji=None, level='subheader'):
    """Render consistent section header with optional emoji"""
    if emoji:
        header_text = f"{emoji} {title}"
    else:
        header_text = title
    
    if level == 'subheader':
        st.subheader(header_text)
    elif level == 'header':
        st.header(header_text)
    else:
        st.markdown(f"**{header_text}**")

def render_navigation_buttons(current_step_key, show_previous=True, show_next=True, custom_previous_label=None, custom_next_label=None):
    """Render consistent navigation buttons at bottom of page"""
    st.markdown("---")
    
    # Get current step info
    current_step = WORKFLOW_STEPS.get(current_step_key)
    if not current_step:
        return
    
    current_number = current_step['number']
    
    # Find previous and next steps
    previous_step = None
    next_step = None
    
    for key, step in WORKFLOW_STEPS.items():
        if step['number'] == current_number - 1:
            previous_step = step
        elif step['number'] == current_number + 1:
            next_step = step
    
    # Create navigation layout
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col1:
        if show_previous and previous_step and current_number > 0:
            prev_label = custom_previous_label or f"← Step {previous_step['number']}"
            if st.button(prev_label, use_container_width=True, key=f"nav_prev_{current_step_key}"):
                st.session_state['current_page'] = previous_step['key']
                st.rerun()
    
    with col2:
        # Center column - could show progress or leave empty
        pass
    
    with col3:
        if show_next and next_step:
            next_label = custom_next_label or f"Step {next_step['number']} →"
            if st.button(next_label, use_container_width=True, key=f"nav_next_{current_step_key}", type="primary"):
                st.session_state['current_page'] = next_step['key']
                st.rerun()

def render_status_message(message, status_type='info'):
    """Render consistent status message with appropriate styling"""
    emoji_map = {
        'success': '✅',
        'warning': '⚠️',
        'error': '❌',
        'info': '💡'
    }
    
    emoji = emoji_map.get(status_type, '💡')
    
    if status_type == 'success':
        st.success(f"{emoji} {message}")
    elif status_type == 'warning':
        st.warning(f"{emoji} {message}")
    elif status_type == 'error':
        st.error(f"{emoji} {message}")
    else:
        st.info(f"{emoji} {message}")

def render_metric_card(label, value, delta=None, help_text=None):
    """Render consistent metric card"""
    st.metric(label=label, value=value, delta=delta, help=help_text)

def render_info_box(title, content, box_type='info'):
    """Render consistent info box with title and content"""
    if box_type == 'info':
        st.info(f"**{title}**\n\n{content}")
    elif box_type == 'warning':
        st.warning(f"**{title}**\n\n{content}")
    elif box_type == 'success':
        st.success(f"**{title}**\n\n{content}")
    elif box_type == 'error':
        st.error(f"**{title}**\n\n{content}")

def render_action_button(label, key, on_click=None, help_text=None, type='primary', use_container_width=True, emoji=None):
    """Render consistent action button"""
    button_label = f"{emoji} {label}" if emoji else label
    return st.button(
        button_label, 
        key=key, 
        on_click=on_click, 
        help=help_text, 
        type=type,
        use_container_width=use_container_width
    )

def render_data_quality_indicator(coverage_percent, label="Data Coverage"):
    """Render consistent data quality indicator"""
    if coverage_percent >= 90:
        st.success(f"✅ {label}: {coverage_percent:.1f}% (Excellent)")
    elif coverage_percent >= 70:
        st.info(f"💡 {label}: {coverage_percent:.1f}% (Good)")
    elif coverage_percent >= 50:
        st.warning(f"⚠️ {label}: {coverage_percent:.1f}% (Adequate)")
    else:
        st.error(f"❌ {label}: {coverage_percent:.1f}% (Insufficient)")

def render_progress_indicator(current_step_number, total_steps=11):
    """Render consistent progress indicator"""
    progress = current_step_number / total_steps
    st.progress(progress)
    st.caption(f"Progress: Step {current_step_number} of {total_steps}")

def render_dependency_check(dependencies_met, missing_dependencies=None):
    """Render consistent dependency check results"""
    st.markdown("### 📋 Dependency Check")
    
    if dependencies_met:
        st.success("✅ All required dependencies are met")
    else:
        st.error("❌ Missing required dependencies")
        if missing_dependencies:
            for dep in missing_dependencies:
                st.warning(f"⚠️ {dep}")

def render_academic_footer():
    """Render consistent academic attribution footer"""
    st.markdown("---")
    st.caption("🎓 **TU Berlin PhD Research** | 🔬 **Authentic Data Standards** | 🚫 **Zero Fallback Tolerance**")

def create_download_button(file_data, filename, label, mime_type='text/csv', emoji='📥'):
    """Create consistent download button"""
    return st.download_button(
        label=f"{emoji} {label}",
        data=file_data,
        file_name=filename,
        mime=mime_type,
        use_container_width=True
    )

def render_expander_section(title, content_func, emoji=None, expanded=False):
    """Render consistent expander section"""
    expander_title = f"{emoji} {title}" if emoji else title
    with st.expander(expander_title, expanded=expanded):
        content_func()

def get_step_info(step_key):
    """Get step information by key"""
    return WORKFLOW_STEPS.get(step_key)

def get_next_step_key(current_step_key):
    """Get next step key"""
    current_step = WORKFLOW_STEPS.get(current_step_key)
    if not current_step:
        return None
    
    current_number = current_step['number']
    for key, step in WORKFLOW_STEPS.items():
        if step['number'] == current_number + 1:
            return key
    return None

def get_previous_step_key(current_step_key):
    """Get previous step key"""
    current_step = WORKFLOW_STEPS.get(current_step_key)
    if not current_step:
        return None
    
    current_number = current_step['number']
    for key, step in WORKFLOW_STEPS.items():
        if step['number'] == current_number - 1:
            return key
    return None
