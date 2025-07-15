# Step 6 PV Specification API Reference

## SpecificationCalculator

### calculate_specifications()

```python
async def calculate_specifications(
    self,
    elements: List[BuildingElement],
    radiation_data: List[RadiationRecord],
    panel_spec: PanelSpecification,
    coverage_factor: float = None,
    performance_ratio: float = None
) -> Tuple[List[ElementPVSpecification], CalculationMetrics]
```

Calculate PV specifications for building elements using vectorized operations.

**Parameters:**
- `elements`: List of building elements from Step 4 facade extraction
- `radiation_data`: List of radiation records from Step 5 analysis
- `panel_spec`: Selected BIPV panel specification
- `coverage_factor`: Panel coverage factor (0-1), defaults to config value
- `performance_ratio`: System performance ratio (0-1), defaults to config value

**Returns:**
- Tuple of (specifications list, calculation metrics)

**Raises:**
- `ValueError`: If input validation fails
- `CalculationError`: If calculation process fails

## PanelCatalogManager

### get_all_panels_async()

```python
async def get_all_panels_async(self) -> List[PanelSpecification]
```

Get all active panels from catalog with optional caching.

### add_panel_async()

```python
async def add_panel_async(self, panel: PanelSpecification) -> Optional[int]
```

Add new panel to catalog with validation and auto-calculation features.

### filter_panels_by_criteria()

```python
def filter_panels_by_criteria(
    self,
    panels: List[PanelSpecification],
    min_efficiency: Optional[float] = None,
    max_efficiency: Optional[float] = None,
    min_transparency: Optional[float] = None,
    max_transparency: Optional[float] = None,
    max_cost: Optional[float] = None,
    panel_types: Optional[List[str]] = None
) -> List[PanelSpecification]
```

Filter panels by multiple criteria for advanced search functionality.

## Database Queries

### bulk_upsert_specifications_async()

```python
async def bulk_upsert_specifications_async(
    self, 
    specifications: List[ElementPVSpecification]
) -> int
```

Efficiently bulk insert/update specifications using PostgreSQL UPSERT operations.

### get_project_specifications_async()

```python
async def get_project_specifications_async(self, project_id: int) -> List[ElementPVSpecification]
```

Retrieve all specifications for a project with joined panel information.

## Configuration Classes

### SpecificationConfig

Settings for PV specification calculations:
- `default_coverage_factor`: Default panel coverage (0.85)
- `default_performance_ratio`: Default system performance (0.85)
- `enable_vectorized_calculations`: Use pandas vectorization (True)
- `large_dataset_threshold`: Threshold for Dask usage (100,000)

### CatalogConfig

Settings for panel catalog management:
- `enable_custom_panels`: Allow custom specifications (True)
- `auto_calculate_power_density`: Auto-calc from efficiency (True)
- `enable_catalog_cache`: LRU caching enabled (True)

## Pydantic Models

### PanelSpecification

```python
class PanelSpecification(BaseModel):
    name: str
    manufacturer: str
    panel_type: PanelType
    efficiency: float  # 0.02-0.25 (2%-25%)
    transparency: float  # 0.0-0.65 (0%-65%)
    power_density: float  # 10-250 W/m²
    cost_per_m2: float  # 50-1000 EUR/m²
    glass_thickness: float  # mm
    u_value: float  # W/m²K
    glass_weight: float  # kg/m²
    performance_ratio: float = 0.85
```

### ElementPVSpecification

```python
class ElementPVSpecification(BaseModel):
    project_id: int
    element_id: str
    panel_spec_id: int
    glass_area: float
    panel_coverage: float
    effective_area: float
    system_power: float  # kW
    annual_radiation: float  # kWh/m²/year
    annual_energy: float  # kWh/year
    specific_yield: float  # kWh/kW/year
    total_cost: float  # EUR
    cost_per_wp: float  # EUR/Wp
    orientation: str
```

## Error Handling

### ValidationError

Raised when input data fails validation:

```python
try:
    specs, metrics = calculator.calculate_specifications(...)
except ValidationError as e:
    print(f"Validation failed: {e.errors}")
```

### CalculationError

Raised when calculation process fails:

```python
try:
    specs, metrics = calculator.calculate_specifications(...)
except CalculationError as e:
    print(f"Calculation failed: {e}")
```

## Utility Functions

### validate_element_radiation_data()

```python
def validate_element_radiation_data(
    elements_df: pd.DataFrame, 
    radiation_df: pd.DataFrame
) -> ValidationResult
```

Validate consistency between building elements and radiation data.

### detect_unit_anomalies()

```python
def detect_unit_anomalies(data: Dict[str, Any]) -> Dict[str, str]
```

Detect potential unit conversion issues in input data.

## Performance Optimization

### Vectorized Calculations

For datasets under 100,000 elements, use vectorized pandas operations:

```python
calculator.use_vectorized = True
specs, metrics = calculator.calculate_specifications(...)
```

### Dask Processing

For large datasets, automatically uses Dask:

```python
# Automatic for >100k elements
specs, metrics = calculator.calculate_specifications(large_dataset...)
```

### Database Connection Pooling

Configure connection pooling for performance:

```python
from step6_pv_spec.config import db_config
db_config.min_connections = 5
db_config.max_connections = 20
```

## Examples

### Basic Usage

```python
from step6_pv_spec import (
    spec_calculator, 
    get_default_panels,
    BuildingElement,
    RadiationRecord
)

# Setup data
panel = get_default_panels()[0]
elements = [BuildingElement(...)]
radiation_data = [RadiationRecord(...)]

# Calculate
specs, metrics = await spec_calculator.calculate_specifications(
    elements=elements,
    radiation_data=radiation_data,
    panel_spec=panel
)

print(f"Processed {metrics.processed_elements} elements in {metrics.calculation_time:.2f}s")
```

### Custom Panel Creation

```python
from step6_pv_spec import panel_catalog_manager, PanelSpecification, PanelType

custom_panel = PanelSpecification(
    name="High-Efficiency BIPV",
    manufacturer="Advanced Solar",
    panel_type=PanelType.SEMI_TRANSPARENT,
    efficiency=0.22,  # 22%
    transparency=0.25,  # 25%
    power_density=220.0,
    cost_per_m2=450.0,
    glass_thickness=8.0,
    u_value=1.5,
    glass_weight=30.0
)

panel_id = await panel_catalog_manager.add_panel_async(custom_panel)
```

### Batch Processing

```python
from step6_pv_spec.db.queries import specification_queries

# Process multiple projects
for project_id in project_ids:
    elements = get_project_elements(project_id)
    radiation = get_project_radiation(project_id)
    
    specs, metrics = await spec_calculator.calculate_specifications(
        elements=elements,
        radiation_data=radiation,
        panel_spec=selected_panel
    )
    
    # Bulk save to database
    await specification_queries.bulk_upsert_specifications_async(specs)
```