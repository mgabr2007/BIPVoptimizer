# Step 5 Radiation Analysis Module

## Overview

This module provides high-performance solar radiation analysis for BIPV (Building Integrated Photovoltaics) optimization. It calculates solar irradiance on building surfaces using authentic meteorological data from Step 3 (TMY) and geometric analysis with multiple analyzer options for different performance needs.

## Key Features

### Three Analyzer Engines
The module includes three specialized radiation analyzers, each optimized for different use cases:

1. **UltraFastRadiationAnalyzer** (`services/ultra_fast_radiation_analyzer.py`)
   - **Processing Time**: 8-15 seconds
   - **Use Case**: Quick preliminary analysis and rapid iterations
   - **Performance**: 82% faster than standard analysis
   - **Method**: Pre-loads all data, vectorized batch processing
   - **Best For**: Yearly Average precision mode

2. **OptimizedRadiationAnalyzer** (`services/optimized_radiation_analyzer.py`)
   - **Processing Time**: 3-5 minutes
   - **Use Case**: Standard production analysis with TMY integration
   - **Performance**: Balanced speed and accuracy
   - **Method**: Precision-based sampling with calculation cache
   - **Best For**: Daily Peak and Monthly Average modes

3. **AdvancedRadiationAnalyzer** (`services/advanced_radiation_analyzer.py`)
   - **Processing Time**: 10-15 minutes
   - **Use Case**: Research-grade comprehensive analysis
   - **Performance**: Maximum accuracy with detailed atmospheric modeling
   - **Method**: Complete hourly calculations with full TMY integration
   - **Best For**: Hourly precision mode (4,015 calculations per element)

### Precision Levels

The module supports four precision levels with different calculation intensities:

| Precision Level | Calculations/Element | Description | Processing Time |
|----------------|---------------------|-------------|-----------------|
| **Hourly** | 4,015 | 11 hours × 365 days - Research grade | 10-15 min |
| **Daily Peak** | 365 | Noon analysis for each day | 3-5 min |
| **Monthly Average** | 12 | Representative day per month | 1-2 min |
| **Yearly Average** | 4 | Seasonal representatives | 8-15 sec |

### Analysis Capabilities

- **Solar Position Calculations**: Accurate sun elevation and azimuth using astronomical algorithms
- **Irradiance Modeling**: DNI, DHI, GHI decomposition with atmospheric corrections
- **Shading Analysis**: Building self-shading and environmental factors
- **Height-Dependent Effects**: Ground reflectance and elevation adjustments
- **TMY Integration**: Authentic meteorological data from Step 3 weather analysis
- **Database Persistence**: Results stored in `element_radiation` table for downstream steps

### User Interface Features

- **Three Calculation Modes**: Simple, Advanced, Auto (intelligent mode selection)
- **Progress Tracking**: Real-time analysis monitoring with completion percentage
- **Results Visualization**: Interactive Plotly charts for orientation analysis
- **Database Check**: Quick validation button to review existing analysis results
- **Performance Metrics**: Display of processing time, elements analyzed, and calculation count

## Module Structure

```
step5_radiation/
├── __init__.py                 # Module exports and interface
├── config.py                   # Analysis configuration and settings
├── models.py                   # Data models for radiation analysis
├── ui.py                       # Streamlit UI components
├── README.md                   # This file
├── requirements.txt            # Python dependencies
│
├── db/                         # Database operations
│   ├── __init__.py
│   └── queries.py             # SQL queries for radiation data
│
├── models/                     # Data models
│   ├── __init__.py
│   └── radiation_models.py    # Pydantic models for validation
│
├── services/                   # Analysis services
│   ├── __init__.py
│   └── analysis_orchestrator.py  # Coordinates analyzer execution
│
├── migrations/                 # Database migrations
│   └── 001_create_radiation_tables.sql
│
└── tests/                     # Test files
    ├── __init__.py
    └── test_radiation_analysis.py
```

## Database Schema

### `radiation_analysis` Table
Stores project-level radiation analysis summary:
```sql
CREATE TABLE radiation_analysis (
    project_id INTEGER PRIMARY KEY,
    avg_irradiance DECIMAL(10,2),
    peak_irradiance DECIMAL(10,2),
    shading_factor DECIMAL(5,2),
    grid_points INTEGER,
    analysis_complete BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### `element_radiation` Table
Stores individual building element radiation results:
```sql
CREATE TABLE element_radiation (
    project_id INTEGER NOT NULL,
    element_id VARCHAR(50) NOT NULL,
    annual_radiation DECIMAL(10,2),
    irradiance DECIMAL(10,2),
    orientation_multiplier DECIMAL(5,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (project_id, element_id)
);
```

## Usage

### Basic Usage in Streamlit Application

The module is integrated into the main BIPV Optimizer workflow as Step 5:

```python
from pages_modules.radiation_grid import render_radiation_grid

# Render radiation analysis interface (called from app.py)
render_radiation_grid()
```

### Execution Flow

The analysis is orchestrated by `services/step5_execution_flow.py`:

```python
from services.step5_execution_flow import Step5ExecutionFlow

# Initialize execution flow
flow = Step5ExecutionFlow(project_id=1)

# Configure analysis
config = {
    'analysis_type': 'optimized',  # 'ultra_fast', 'optimized', or 'advanced'
    'precision': 'Daily Peak',      # Precision level
    'apply_corrections': True,      # Apply atmospheric corrections
    'include_shading': True,        # Include shading analysis
    'calculation_mode': 'auto'      # Auto-select best analyzer
}

# Execute analysis
result = flow.run_analysis(config)

if result['success']:
    print(f"Analyzed {result['results']['total_elements']} elements")
    print(f"Processing time: {result['results']['calculation_time']:.2f} seconds")
```

### Direct Analyzer Usage

You can also use analyzers directly for specialized workflows:

```python
from services.ultra_fast_radiation_analyzer import UltraFastRadiationAnalyzer

# Initialize analyzer
analyzer = UltraFastRadiationAnalyzer()

# Run analysis
results = analyzer.analyze_project_radiation(
    project_id=1,
    precision="Simple",
    apply_corrections=True,
    include_shading=True
)

# Access results
for element in results['element_radiation']:
    print(f"Element {element['element_id']}: {element['annual_radiation']} kWh/m²/year")
```

## Prerequisites

### Required Steps
Before running radiation analysis, these workflow steps must be completed:
1. **Step 1 - Project Setup**: Location and project data
2. **Step 3 - Weather Integration**: TMY data generation
3. **Step 4 - BIM Extraction**: Building elements with PV suitability flags

### Python Dependencies
```bash
# Core dependencies (from main project)
streamlit >= 1.46.0
pandas >= 2.0.3
numpy >= 1.24.4
plotly >= 6.1.2
pvlib >= 0.13.0
psycopg2-binary >= 2.9.10
pytz >= 2025.2

# Scientific computing
scikit-learn >= 1.7.0
```

## Configuration

The module uses `config.py` for analysis settings:

```python
# Analysis precision configurations
PRECISION_CONFIGS = {
    "Hourly": {
        "sample_hours": list(range(8, 19)),  # 8 AM to 6 PM
        "days_per_month": 365,
        "accuracy": "Maximum",
        "sample_size": 4015
    },
    "Daily Peak": {
        "sample_hours": [12],  # Noon only
        "days_per_month": 365,
        "accuracy": "High",
        "sample_size": 365
    },
    "Monthly Average": {
        "sample_hours": [12],
        "days_per_month": 12,
        "accuracy": "Standard",
        "sample_size": 12
    },
    "Yearly Average": {
        "sample_hours": [12],
        "days_per_month": 4,
        "accuracy": "Fast",
        "sample_size": 4
    }
}
```

## Performance Optimization

### Memory Management
- **Pre-loading**: All project data loaded once to minimize database calls
- **Vectorized Processing**: NumPy batch operations instead of loops
- **Cache System**: Calculation results cached to avoid redundant computations

### Database Optimization
- **Bulk Operations**: Batch inserts for element radiation data
- **Connection Pooling**: Efficient database connection management
- **Indexed Queries**: Optimized indices on `project_id` and `element_id`

### Processing Speed Comparison
Based on 756 building elements:
- **UltraFast**: ~8 seconds (Yearly Average mode)
- **Optimized**: ~180 seconds (Daily Peak mode)
- **Advanced**: ~600 seconds (Hourly mode)

## Data Flow

### Input Requirements
1. **Project Location**: Latitude, longitude from Step 1
2. **TMY Data**: Hourly meteorological data from Step 3
3. **Building Elements**: Window/facade data with orientations from Step 4

### Output Data
The analysis produces:
1. **Element Radiation**: Annual radiation for each building element (kWh/m²/year)
2. **Summary Statistics**: Average/peak irradiance, shading factors
3. **Orientation Analysis**: Performance breakdown by facade orientation
4. **Performance Metrics**: Processing time, calculation count, elements analyzed

### Downstream Usage
Step 5 results are used by:
- **Step 6**: BIPV glass specification (requires radiation data)
- **Step 7**: Yield vs demand analysis (requires radiation data)
- **Step 8**: Multi-objective optimization (requires radiation data)
- **Step 9**: Financial analysis (indirectly through optimization results)

## Error Handling

The module implements comprehensive error handling:

```python
# Validation checks performed:
- Project ID validation
- TMY data availability check
- Building elements existence check
- PV-suitable elements validation
- Orientation data completeness
- Glass area data validation

# Error scenarios:
- Missing TMY data → Clear error message with Step 3 guidance
- No building elements → Redirect to Step 4
- No PV-suitable elements → Guidance on facade selection
- Database connection issues → Graceful failure with retry option
```

## Calculation Methodology

### Solar Position
- **Algorithm**: NREL Solar Position Algorithm (SPA)
- **Inputs**: Latitude, longitude, date/time, timezone
- **Outputs**: Solar elevation, azimuth angles

### Irradiance Components
- **GHI**: Global Horizontal Irradiance from TMY data
- **DNI**: Direct Normal Irradiance (decomposed from GHI)
- **DHI**: Diffuse Horizontal Irradiance (calculated residual)

### Surface Irradiance
- **Orientation Factor**: Cosine of incidence angle
- **Shading Factor**: Environmental and self-shading effects
- **Ground Reflectance**: Albedo-based reflected radiation
- **Atmospheric Corrections**: Air mass and elevation adjustments

### Annual Integration
```python
# Calculation formula
annual_radiation = sum(
    hourly_irradiance * orientation_factor * shading_factor
    for each_timestamp in year
) * scaling_factor
```

## Known Limitations

1. **TMY Dependency**: Requires completed Step 3 weather analysis
2. **Element Filtering**: Only analyzes PV-suitable elements (pv_suitable=true)
3. **Orientation Range**: Optimized for South/East/West facades (configurable)
4. **Processing Time**: Hourly precision mode can take 10-15 minutes for large buildings
5. **Database Storage**: Large result sets may require database optimization

## Troubleshooting

### "No TMY data found"
**Solution**: Complete Step 3 (Weather Integration) first to generate TMY data.

### "No PV-suitable elements found"
**Solution**: Upload BIM data in Step 4 and ensure elements are marked as PV-suitable.

### Analysis taking too long
**Solution**: Switch to lower precision mode (Monthly Average or Yearly Average) for faster results.

### Memory errors with large buildings
**Solution**: Process in smaller batches or increase system memory allocation.

## License

This module is part of the BIPV Optimizer platform developed for academic research at Technische Universität Berlin.

**Research Context**: PhD research by Mostafa Gabr  
**Institution**: Technische Universität Berlin, Faculty VI - Planning Building Environment  
**ResearchGate**: https://www.researchgate.net/profile/Mostafa-Gabr-4

## Contact

For technical questions or research collaboration:
- **Developer**: BIPV Optimizer Development Team
- **Institution**: Technische Universität Berlin
- **Faculty**: Planning Building Environment (VI)
- **Primary Researcher**: Mostafa Gabr

---

**Part of BIPV Optimizer - Building-Integrated Photovoltaics Analysis Platform**
