import streamlit as st

st.set_page_config(
    page_title="BIPV Optimizer",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("🏢 BIPV Optimizer")
st.write("Testing basic Streamlit functionality...")

# Test if we can import numpy specifically
try:
    import numpy as np
    st.success(f"✅ NumPy imported successfully! Version: {np.__version__}")
except Exception as e:
    st.error(f"❌ NumPy import failed: {str(e)}")

# Test pandas import
try:
    import pandas as pd
    st.success(f"✅ Pandas imported successfully! Version: {pd.__version__}")
except Exception as e:
    st.error(f"❌ Pandas import failed: {str(e)}")

# Test other dependencies
try:
    import plotly.graph_objects as go
    st.success("✅ Plotly imported successfully!")
except Exception as e:
    st.error(f"❌ Plotly import failed: {str(e)}")

st.write("If all dependencies load successfully, the full BIPV Optimizer will work.")