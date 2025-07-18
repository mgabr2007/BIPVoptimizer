"""
Step 10: Comprehensive BIPV Analysis Dashboard
Real-time dashboard displaying all calculated data from all workflow steps
"""
import streamlit as st
from pages_modules.comprehensive_dashboard import render_comprehensive_dashboard

def render_reporting():
    """Render the comprehensive BIPV analysis dashboard"""
    render_comprehensive_dashboard()