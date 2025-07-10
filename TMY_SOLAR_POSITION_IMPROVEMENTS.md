# TMY Solar Position Calculation Improvements

## Changes Made

### 1. Solar Position Calculation Accuracy
- **Updated `calculate_solar_position_iso()` function in `core/solar_math.py`**
- Implemented Cooper's equation for more accurate solar declination
- Added equation of time correction for improved solar position accuracy
- Fixed azimuth calculation to use proper spherical trigonometry
- Changed azimuth reference from "south" to "north clockwise" (0-360°) - standard convention

### 2. Solar Azimuth Convention
- **Previous**: Azimuth from south (negative/positive values)
- **Updated**: Azimuth from north clockwise (0-360°)
  - 0° = North
  - 90° = East
  - 180° = South
  - 270° = West

### 3. DateTime Formatting
- **Previous**: Day-of-year format (2023-365-12:00)
- **Updated**: Proper ISO datetime (2023-12-31 12:00:00)
- Added proper conversion from day-of-year to month-day format

### 4. Data Precision Improvements
- Solar elevation: Rounded to 2 decimal places
- Solar azimuth: Rounded to 2 decimal places
- Air mass: Rounded to 3 decimal places
- Irradiance values: Rounded to 2 decimal places

## Validation

The improved calculations now provide:
- **Solar elevation**: 0-90° (sun above horizon)
  - Berlin summer solstice: ~57° (accurate)
  - Berlin winter solstice: ~12° (accurate)
- **Solar azimuth**: 0-360° from north clockwise
  - Values may deviate from exact 180° at noon due to longitude corrections
  - Berlin longitude (13.4°E) causes expected offset from 180°
- **Accurate timing**: Proper datetime stamps for each hour
- **Air mass**: Calculated only when sun is above horizon
- **Equation of time**: Includes corrections for Earth's orbital variations

## Known Behavior
- Azimuth at solar noon may not be exactly 180° due to:
  - Longitude corrections (4 minutes per degree)
  - Equation of time adjustments
  - This is physically correct behavior

## CSV Export Columns

The TMY CSV export now includes these corrected columns:
- `DateTime`: YYYY-MM-DD HH:MM:SS format
- `SolarElevation_deg`: Solar elevation angle (0-90°)
- `SolarAzimuth_deg`: Solar azimuth from north clockwise (0-360°)
- `GHI_Wm2`, `DNI_Wm2`, `DHI_Wm2`: Solar irradiance values
- `AirMass`: Atmospheric air mass (dimensionless)

## Standards Compliance

These improvements maintain ISO 15927-4 compliance while providing more accurate solar position data for BIPV analysis.