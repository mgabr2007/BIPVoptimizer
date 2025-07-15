# Step 4 Facade Extraction - Production Grade Module

## Overview

This module provides a production-grade implementation of building facade and window data extraction for BIPV (Building Integrated Photovoltaics) analysis. It transforms raw BIM data into structured, validated, and analysis-ready datasets.

## Features

### 🏗️ Architecture
- **Modular Design**: Separated UI, processing, database, and validation concerns
- **Type Safety**: Full Pydantic models with validation
- **Async Support**: Asynchronous database operations for better performance
- **Configuration**: YAML-based configuration management

### 🚀 Performance
- **Chunked Processing**: Memory-efficient processing of large CSV files
- **Bulk Operations**: Optimized database UPSERT operations
- **Parallel Processing**: Multi-threaded file processing capabilities
- **Progress Tracking**: Real-time progress indicators with ETA

### 🔍 Data Quality
- **Schema Validation**: Pandera-based DataFrame validation
- **Unit Detection**: Automatic detection and conversion suggestions
- **Duplicate Detection**: ElementId uniqueness validation
- **Locale Support**: Handles comma decimal separators

### 🛡️ Security & Reliability
- **File Validation**: Size, extension, and MIME type checks
- **Malware Scanning**: Optional security scanning
- **Error Handling**: Comprehensive error collection and reporting
- **Logging**: Structured logging with context

## Installation

### Dependencies

```bash
pip install -r requirements.txt
```

Required packages:
- `streamlit` - Web interface
- `pandas` - Data manipulation
- `pydantic` - Data validation
- `pandera` - DataFrame schema validation
- `psycopg2-binary` - PostgreSQL adapter
- `asyncpg` - Async PostgreSQL adapter
- `plotly` - Data visualization
- `loguru` - Structured logging
- `pyyaml` - Configuration files

### Database Setup

Ensure PostgreSQL is running and the following tables exist:

```sql
-- Building elements (windows/glazing)
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

-- Building walls
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

-- Indices for performance
CREATE INDEX idx_building_elements_project_id ON building_elements(project_id);
CREATE INDEX idx_building_elements_element_id ON building_elements(element_id);
CREATE INDEX idx_building_walls_project_id ON building_walls(project_id);
```

## Usage

### Basic Usage

```python
from step4_facade_extraction import render_facade_extraction

# Render the complete interface
render_facade_extraction(project_id=1)
```

### Advanced Usage

```python
from step4_facade_extraction import (
    DataProcessor, BulkDatabaseOperations, 
    get_config, WindowRecord
)

# Initialize components
config = get_config()
processor = DataProcessor(project_id=1)
db_ops = BulkDatabaseOperations(project_id=1)

# Process CSV file
with open('windows.csv', 'rb') as f:
    file_content = f.read()

result = processor.process_csv_file(
    'windows.csv', file_content, 'windows'
)

if result.success:
    print(f"Processed {result.processed_elements} elements")
    print(f"Found {result.suitable_elements} PV-suitable elements")
```

### Configuration

Edit `step4_facade_extraction/config.yaml` to customize:

```yaml
# PV Suitability Rules
suitability:
  min_glass_area: 0.5
  max_glass_area: 100.0
  suitable_orientations:
    - "South"
    - "East"
    - "West"

# Processing Settings
processing:
  chunk_size: 500
  max_file_size_mb: 50

# Database Settings
database:
  batch_size: 1000
  connection_timeout: 30
```

## Data Formats

### Window Elements CSV

Required columns:
- `ElementId` - Unique element identifier
- `Family` - Window family/type name
- `Glass Area (m²)` - Glass area in square meters
- `Azimuth (°)` - Azimuth angle (0-360 degrees)

Optional columns:
- `Level` - Building level/floor
- `HostWallId` - Associated wall element ID
- `Window Width (m)` - Window width in meters
- `Window Height (m)` - Window height in meters

### Wall Elements CSV

Required columns:
- `ElementId` - Unique wall identifier
- `Wall Type` - Wall type/family name
- `Length (m)` - Wall length in meters
- `Area (m²)` - Wall area in square meters
- `Azimuth (°)` - Wall azimuth (0-360 degrees)

Optional columns:
- `Level` - Building level/floor

## Testing

Run the test suite:

```bash
# Install test dependencies
pip install pytest pytest-asyncio

# Run tests
pytest step4_facade_extraction/tests/ -v

# Run with coverage
pytest step4_facade_extraction/tests/ --cov=step4_facade_extraction --cov-report=html
```

### Test Structure

```
tests/
├── __init__.py
├── test_processing.py      # Data processing tests
├── test_database.py        # Database operation tests  
├── test_validation.py      # Data validation tests
├── test_ui.py             # UI component tests
└── conftest.py            # Test fixtures
```

## API Reference

### Core Classes

#### `DataProcessor`
Main data processing class with chunked processing capabilities.

**Methods:**
- `process_csv_file(filename, content, data_type, progress_callback)` - Process CSV file
- `get_orientation_from_azimuth(azimuth)` - Convert azimuth to orientation
- `determine_pv_suitability(orientation, area, family)` - Check PV suitability

#### `BulkDatabaseOperations`
High-performance database operations.

**Methods:**
- `bulk_upsert_windows(windows)` - Bulk insert/update windows
- `bulk_upsert_walls(walls)` - Bulk insert/update walls
- `check_duplicates_in_db(project_id, element_ids, table)` - Check for duplicates

#### `DataFrameValidator`
Data validation using Pandera schemas.

**Methods:**
- `validate_window_data(df)` - Validate window DataFrame
- `validate_wall_data(df)` - Validate wall DataFrame
- `detect_units(df, column)` - Detect unit conversion needs

### Data Models

#### `WindowRecord`
Pydantic model for window elements with full validation.

#### `WallRecord`
Pydantic model for wall elements with calculated properties.

#### `ProcessingResult`
Processing outcome with performance metrics and error tracking.

## Development Workflow

### Pre-commit Setup

```bash
# Install pre-commit
pip install pre-commit

# Install hooks
pre-commit install

# Run manually
pre-commit run --all-files
```

### Code Quality

The module uses:
- **Black** - Code formatting
- **Ruff** - Linting and import sorting
- **MyPy** - Type checking
- **Pytest** - Testing framework

### Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Run pre-commit hooks
6. Submit a pull request

## Performance Optimization

### Memory Usage
- Chunked CSV processing prevents memory overflow
- Session state cleanup after operations
- Streaming database operations

### Database Performance
- UPSERT operations instead of DELETE+INSERT
- Bulk operations with configurable batch sizes
- Connection pooling and context managers
- Optimized indices on frequently queried columns

### UI Responsiveness
- Async database operations
- Progress tracking with real-time updates
- Lazy loading of large datasets
- Client-side validation before upload

## Monitoring & Logging

### Structured Logging
```python
from step4_facade_extraction.logging_utils import get_logger

logger = get_logger(project_id=1)
logger.info("Processing started", operation="csv_upload", file_size=12345)
```

### Error Monitoring
Configure Sentry or similar service:
```python
from step4_facade_extraction.logging_utils import setup_error_monitoring
setup_error_monitoring()
```

### Performance Metrics
Monitor processing rates, success rates, and timing:
```python
from step4_facade_extraction.ui import render_performance_metrics
render_performance_metrics(processing_result)
```

## Troubleshooting

### Common Issues

**Import Errors**
- Ensure all dependencies are installed
- Check Python version compatibility (3.11+)

**Database Connection Issues**
- Verify PostgreSQL is running
- Check connection parameters in environment variables
- Ensure database schema is up to date

**Memory Issues with Large Files**
- Increase chunk_size in configuration
- Monitor system memory usage
- Consider processing files in smaller batches

**Validation Failures**
- Check CSV column names match exactly
- Verify data types (numeric vs text)
- Look for special characters or encoding issues

### Debug Mode

Enable debug mode in configuration:
```yaml
ui:
  enable_debug_mode: true
```

This shows:
- Raw configuration values
- Processing logs in real-time
- Detailed error tracebacks
- Performance metrics

## License

This module is part of the BIPV Optimizer platform developed for academic research at Technische Universität Berlin.

## Contact

For technical support or questions:
- **Author**: BIPV Optimizer Development Team
- **Institution**: Technische Universität Berlin
- **Faculty**: Planning Building Environment (VI)