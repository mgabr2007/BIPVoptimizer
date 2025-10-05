# Step 4 Facade Extraction Module

## Overview

This module handles building facade and window data extraction for BIPV (Building Integrated Photovoltaics) analysis. It processes CSV files extracted from BIM models (Revit/CAD via Dynamo scripts) and transforms them into analysis-ready datasets with automated BIPV suitability assessment based on orientation and architectural constraints.

## Key Features

### Data Processing
- **BIM CSV Upload**: Supports window and wall element data from Dynamo script exports
- **Multi-Format Support**: Handles various CSV column naming conventions
- **Chunked Processing**: Memory-efficient processing of large BIM datasets
- **Data Validation**: Comprehensive error checking and type validation

### BIPV Suitability Assessment
- **Orientation-Based Filtering**: Automatic identification of South/East/West-facing elements
- **Exclusion Rules**: Filters out north-facing and unsuitable window types
- **Historical Preservation**: Considers architectural constraints (configurable)
- **Glass Area Validation**: Ensures minimum area requirements for PV installation

### Database Integration
- **PostgreSQL Storage**: Persistent storage in `building_elements` and `building_walls` tables
- **Duplicate Prevention**: Automatic handling of re-uploads without duplication
- **Bulk Operations**: High-performance batch inserts with UPSERT logic
- **Element Tracking**: Unique element IDs linked to project IDs

### User Interface
- **Streamlit Interface**: Clean upload interface with drag-and-drop support
- **Progress Tracking**: Real-time upload and processing status
- **Data Preview**: Displays processed elements with suitability indicators
- **Statistics Dashboard**: Summary of elements, orientations, and PV-suitable count

## Module Structure

```
step4_facade_extraction/
├── __init__.py                 # Module exports
├── config.py                   # Configuration management
├── config.yaml                 # YAML configuration file
├── models.py                   # Pydantic data models
├── processing.py               # Data processing logic
├── database.py                 # Database operations
├── validators.py               # Data validation
├── ui.py                       # Streamlit UI components
├── logging_utils.py            # Logging configuration
├── README.md                   # This file
│
├── config/                     # Configuration submodule
│   ├── __init__.py
│   └── settings.py            # Settings management
│
├── models/                     # Data models submodule
│   ├── __init__.py
│   ├── window_record.py       # Window element model
│   └── wall_record.py         # Wall element model
│
├── processing/                 # Processing submodule
│   ├── __init__.py
│   ├── data_processor.py      # Main CSV processor
│   └── orientation_calculator.py  # Azimuth to orientation conversion
│
├── database/                   # Database submodule
│   ├── __init__.py
│   ├── bulk_operations.py     # Bulk insert/update operations
│   └── queries.py             # SQL query builders
│
├── validators/                 # Validation submodule
│   ├── __init__.py
│   └── dataframe_validator.py # Pandera schema validation
│
├── ui/                        # UI submodule
│   ├── __init__.py
│   ├── upload_component.py    # File upload interface
│   └── results_display.py     # Results visualization
│
├── logging_utils/             # Logging submodule
│   ├── __init__.py
│   └── logger_config.py       # Loguru configuration
│
└── tests/                     # Test files
    ├── __init__.py
    └── test_processing.py     # Processing tests
```

## Database Schema

### `building_elements` Table
Stores window and glazing elements suitable for BIPV analysis:

```sql
CREATE TABLE building_elements (
    id SERIAL PRIMARY KEY,
    project_id INTEGER NOT NULL,
    element_id VARCHAR(50) NOT NULL,
    family VARCHAR(100),
    element_type VARCHAR(50),
    glass_area DECIMAL(10,2),
    window_width DECIMAL(10,2),
    window_height DECIMAL(10,2),
    building_level VARCHAR(20),
    wall_element_id VARCHAR(50),
    azimuth DECIMAL(5,1),
    orientation VARCHAR(20),
    pv_suitable BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(project_id, element_id)
);

CREATE INDEX idx_building_elements_project_id ON building_elements(project_id);
CREATE INDEX idx_building_elements_pv_suitable ON building_elements(project_id, pv_suitable);
```

### `building_walls` Table
Stores wall elements for contextual information:

```sql
CREATE TABLE building_walls (
    id SERIAL PRIMARY KEY,
    project_id INTEGER NOT NULL,
    element_id VARCHAR(50) NOT NULL,
    name VARCHAR(100),
    wall_type VARCHAR(100),
    level VARCHAR(20),
    area DECIMAL(10,2),
    azimuth DECIMAL(5,1),
    orientation VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(project_id, element_id)
);

CREATE INDEX idx_building_walls_project_id ON building_walls(project_id);
```

## Usage

### In Main Application (app.py)

The module is integrated as Step 4 in the main workflow:

```python
from pages_modules.facade_extraction import render_facade_extraction

# Render facade extraction interface
render_facade_extraction()
```

### Programmatic Usage

```python
from step4_facade_extraction import DataProcessor, BulkDatabaseOperations

# Initialize processor
processor = DataProcessor(project_id=1)

# Process uploaded CSV file
with open('windows.csv', 'rb') as f:
    file_content = f.read()

result = processor.process_csv_file(
    filename='windows.csv',
    content=file_content,
    data_type='windows'
)

if result.success:
    print(f"✅ Processed {result.processed_elements} elements")
    print(f"✅ Found {result.suitable_elements} PV-suitable windows")
    print(f"⚡ Processing time: {result.processing_time:.2f}s")
else:
    print(f"❌ Error: {result.error_message}")
```

## Configuration

### YAML Configuration (config.yaml)

```yaml
# PV Suitability Rules
suitability:
  min_glass_area: 0.5          # Minimum area in m² for PV installation
  max_glass_area: 100.0        # Maximum area in m²
  suitable_orientations:        # Facade orientations suitable for BIPV
    - "South"
    - "Southeast" 
    - "Southwest"
    - "East"
    - "West"
  excluded_families:            # Window families to exclude
    - "Historic Window"
    - "Fixed Window - Small"

# Processing Settings
processing:
  chunk_size: 500               # Elements per processing chunk
  max_file_size_mb: 50          # Maximum upload file size

# Database Settings
database:
  batch_size: 1000              # Records per batch insert
  connection_timeout: 30         # Connection timeout in seconds
```

### Python Configuration

```python
from step4_facade_extraction import get_config

# Load configuration
config = get_config()

# Access settings
min_area = config.suitability.min_glass_area
orientations = config.suitability.suitable_orientations
```

## Data Formats

### Window Elements CSV Format

**Required Columns:**
- `ElementId` - Unique element identifier from BIM model
- `Family` - Window family/type name
- `Glass Area (m²)` - Glass area in square meters
- `Azimuth (°)` - Azimuth angle (0-360 degrees)

**Optional Columns:**
- `Level` - Building level/floor (e.g., "Level 1", "Ground Floor")
- `HostWallId` - Associated wall element ID
- `Window Width (m)` - Window width in meters
- `Window Height (m)` - Window height in meters

**Example CSV:**
```csv
ElementId,Family,Glass Area (m²),Azimuth (°),Level,Window Width (m),Window Height (m)
W-001,Curtain Wall,3.50,180,Level 1,2.0,1.75
W-002,Fixed Window,1.20,90,Level 2,1.2,1.0
W-003,Operable Window,2.80,270,Level 1,1.6,1.75
```

### Wall Elements CSV Format

**Required Columns:**
- `ElementId` - Unique wall identifier
- `Wall Type` - Wall type/family name
- `Length (m)` - Wall length in meters
- `Area (m²)` - Wall area in square meters
- `Azimuth (°)` - Wall azimuth (0-360 degrees)

**Optional Columns:**
- `Level` - Building level/floor

**Example CSV:**
```csv
ElementId,Wall Type,Length (m),Area (m²),Azimuth (°),Level
WALL-001,Exterior Wall - Brick,12.5,37.5,180,Level 1
WALL-002,Curtain Wall,8.0,24.0,90,Level 1
```

## Suitability Assessment Logic

### Orientation Calculation
```python
def get_orientation_from_azimuth(azimuth: float) -> str:
    """
    Convert azimuth angle to cardinal/intercardinal orientation.
    
    Azimuth ranges:
    - North: 337.5° - 22.5°
    - Northeast: 22.5° - 67.5°
    - East: 67.5° - 112.5°
    - Southeast: 112.5° - 157.5°
    - South: 157.5° - 202.5°
    - Southwest: 202.5° - 247.5°
    - West: 247.5° - 292.5°
    - Northwest: 292.5° - 337.5°
    """
```

### PV Suitability Rules
An element is marked as `pv_suitable=true` if:
1. ✅ Orientation is in suitable list (South, East, West, SE, SW)
2. ✅ Glass area ≥ minimum threshold (default 0.5 m²)
3. ✅ Glass area ≤ maximum threshold (default 100 m²)
4. ✅ Family is not in exclusion list
5. ✅ Element type is window/curtain wall/glazing

## Processing Workflow

### Step-by-Step Execution

1. **File Upload**
   - User uploads CSV via Streamlit file uploader
   - File size validation (max 50 MB)
   - MIME type checking

2. **CSV Parsing**
   - Pandas DataFrame creation
   - Column name normalization
   - Data type conversion

3. **Data Validation**
   - Required column presence check
   - Numeric value validation
   - Range validation (azimuth 0-360°)

4. **Orientation Processing**
   - Azimuth to orientation conversion
   - Suitability assessment per element
   - Family-based exclusion filtering

5. **Database Storage**
   - Duplicate check (project_id + element_id)
   - Bulk UPSERT operation
   - Transaction commit with rollback on error

6. **Results Display**
   - Summary statistics
   - PV-suitable element count
   - Orientation distribution chart

## Performance Characteristics

### Processing Speed
- **Small buildings** (<100 elements): <1 second
- **Medium buildings** (100-500 elements): 1-3 seconds
- **Large buildings** (500-2000 elements): 3-10 seconds
- **Very large buildings** (>2000 elements): 10-30 seconds

### Memory Usage
- Chunked processing prevents memory overflow
- Configurable chunk size (default 500 elements)
- Streaming database inserts

### Database Performance
- UPSERT operations prevent duplication
- Bulk inserts with batch size 1000
- Indexed queries on project_id and pv_suitable

## Error Handling

### Common Error Scenarios

**Missing Required Columns**
```
Error: CSV missing required columns: ['ElementId', 'Glass Area (m²)']
Solution: Ensure Dynamo export includes all required fields
```

**Invalid Azimuth Values**
```
Warning: 5 elements have azimuth values outside 0-360° range
Action: Values automatically normalized to valid range
```

**Database Connection Failure**
```
Error: Cannot connect to database
Solution: Check DATABASE_URL environment variable and PostgreSQL service
```

**Duplicate Elements**
```
Warning: 12 elements already exist for project 1
Action: Existing elements updated with new data (UPSERT)
```

## Integration with Workflow

### Prerequisites
Before using this module, complete:
1. **Step 1 - Project Setup**: Project ID and location data

### Downstream Dependencies
Step 4 data is required by:
2. **Step 5 - Radiation Analysis**: Uses PV-suitable elements with orientations
3. **Step 6 - PV Specification**: Applies BIPV glass to suitable elements
4. **Step 7 - Yield Analysis**: Calculates energy production per element
5. **Step 8 - Optimization**: Selects optimal element subset

## Data Extraction from BIM

### Revit Dynamo Script

The module expects CSV files generated by Dynamo scripts. Example script workflow:

1. **Select Window Elements**
   - Filter by category (Windows, Curtain Panels)
   - Collect element instances

2. **Extract Properties**
   - Element ID (UniqueId or ElementId)
   - Family name
   - Type parameters (Width, Height)
   - Instance parameters (Level, Host Wall)
   - Calculated properties (Glass Area, Azimuth)

3. **Export to CSV**
   - Structure data as table
   - Write to CSV with proper headers
   - Include units in column names

Sample Dynamo export script available in `attached_assets/get_windowMetadata_*.dyn`

## Known Limitations

1. **CSV-Only Format**: Currently supports only CSV input (no IFC, gbXML)
2. **Manual Upload**: Requires manual file upload (no API integration)
3. **Single Project**: Processes one project at a time
4. **Orientation Granularity**: Uses 8-point cardinal system (N, NE, E, SE, S, SW, W, NW)
5. **No Geometry**: Does not process 3D geometry, only metadata

## Future Enhancements

Potential improvements (not currently implemented):
- Direct IFC file import
- Automatic Dynamo script generation
- Multi-project batch processing
- 3D geometry visualization
- Shading analysis from geometry
- Wall-window relationship validation

## Troubleshooting

### CSV Upload Fails
**Check:**
- File size under 50 MB
- File is valid CSV format
- Encoding is UTF-8
- No special characters in headers

### No PV-Suitable Elements Found
**Causes:**
- All elements face North (excluded by default)
- Glass areas below minimum threshold
- Window families in exclusion list
- Missing azimuth data

**Solution:**
- Review suitability configuration in config.yaml
- Check building orientation
- Verify Dynamo export includes all required fields

### Database Errors
**Common Issues:**
- Missing DATABASE_URL environment variable
- PostgreSQL service not running
- Table schema not created
- Insufficient permissions

**Solution:**
- Verify database connection string
- Run schema creation SQL
- Check PostgreSQL logs

## License

This module is part of the BIPV Optimizer platform developed for academic research at Technische Universität Berlin.

**Research Context**: PhD research by Mostafa Gabr  
**Institution**: Technische Universität Berlin, Faculty VI - Planning Building Environment  
**ResearchGate**: https://www.researchgate.net/profile/Mostafa-Gabr-4

## Contact

For technical support or research collaboration:
- **Developer**: BIPV Optimizer Development Team
- **Institution**: Technische Universität Berlin
- **Faculty**: Planning Building Environment (VI)
- **Primary Researcher**: Mostafa Gabr

---

**Part of BIPV Optimizer - Building-Integrated Photovoltaics Analysis Platform**
