#!/usr/bin/env python3
"""Test script to verify package imports"""

import sys
import os

# Test basic imports
try:
    import streamlit as st
    print("✓ Streamlit imported successfully")
except ImportError as e:
    print(f"✗ Streamlit import failed: {e}")

try:
    import numpy as np
    print(f"✓ NumPy {np.__version__} imported successfully")
except ImportError as e:
    print(f"✗ NumPy import failed: {e}")

try:
    import pandas as pd
    print(f"✓ Pandas {pd.__version__} imported successfully")
except ImportError as e:
    print(f"✗ Pandas import failed: {e}")

try:
    import plotly
    print(f"✓ Plotly {plotly.__version__} imported successfully")
except ImportError as e:
    print(f"✗ Plotly import failed: {e}")

try:
    from sklearn.ensemble import RandomForestRegressor
    print("✓ Scikit-learn imported successfully")
except ImportError as e:
    print(f"✗ Scikit-learn import failed: {e}")

try:
    import pvlib
    print(f"✓ PVLib {pvlib.__version__} imported successfully")
except ImportError as e:
    print(f"✗ PVLib import failed: {e}")

try:
    import deap
    print(f"✓ DEAP {deap.__version__} imported successfully")
except ImportError as e:
    print(f"✗ DEAP import failed: {e}")

print("\nPython path:")
for path in sys.path:
    print(f"  {path}")