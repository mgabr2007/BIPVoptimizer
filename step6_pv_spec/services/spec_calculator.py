"""
BIPV sizing and cost calculation service with vectorized operations.
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
import logging
from datetime import datetime
import dask.dataframe as dd
from functools import lru_cache

from ..models import (
    BuildingElement, RadiationRecord, PanelSpecification, 
    ElementPVSpecification, ProjectPVSummary, CalculationMetrics,
    ValidationResult
)
from ..config import (
    spec_config, VALIDATION_RANGES, COST_PARAMETERS, 
    ORIENTATION_FACTORS, UNIT_CONVERSIONS
)

logger = logging.getLogger(__name__)


class SpecificationCalculator:
    """High-performance BIPV specification calculator with vectorized operations."""
    
    def __init__(self):
        self.config = spec_config
        self.use_vectorized = self.config.enable_vectorized_calculations
        self.large_threshold = self.config.large_dataset_threshold
        
    def calculate_specifications(
        self,
        elements: List[BuildingElement],
        radiation_data: List[RadiationRecord],
        panel_spec: PanelSpecification,
        coverage_factor: float = None,
        performance_ratio: float = None
    ) -> Tuple[List[ElementPVSpecification], CalculationMetrics]:
        """
        Calculate PV specifications for building elements.
        
        Args:
            elements: List of building elements
            radiation_data: List of radiation records
            panel_spec: Selected panel specification
            coverage_factor: Panel coverage factor (0-1)
            performance_ratio: System performance ratio (0-1)
            
        Returns:
            Tuple of (specifications, metrics)
        """
        start_time = datetime.now()
        
        # Set defaults
        coverage_factor = coverage_factor or self.config.default_coverage_factor
        performance_ratio = performance_ratio or self.config.default_performance_ratio
        
        try:
            # Convert to DataFrames for vectorized operations
            elements_df = self._elements_to_dataframe(elements)
            radiation_df = self._radiation_to_dataframe(radiation_data)
            
            # Validate input data
            validation = self._validate_input_data(elements_df, radiation_df)
            if not validation.is_valid:
                raise ValueError(f"Input validation failed: {validation.errors}")
            
            # Merge data
            merged_df = self._merge_element_radiation_data(elements_df, radiation_df)
            
            # Choose calculation method based on dataset size
            if len(merged_df) > self.large_threshold and self.config.use_dask_for_large_datasets:
                specifications = self._calculate_with_dask(
                    merged_df, panel_spec, coverage_factor, performance_ratio
                )
                method = "dask"
            elif self.use_vectorized:
                specifications = self._calculate_vectorized(
                    merged_df, panel_spec, coverage_factor, performance_ratio
                )
                method = "vectorized"
            else:
                specifications = self._calculate_iterative(
                    merged_df, panel_spec, coverage_factor, performance_ratio
                )
                method = "iterative"
            
            calculation_time = (datetime.now() - start_time).total_seconds()
            
            # Create metrics
            metrics = CalculationMetrics(
                total_elements=len(elements),
                processed_elements=len(specifications),
                calculation_time=calculation_time,
                method_used=method,
                errors_encountered=len(elements) - len(specifications)
            )
            
            logger.info(f"Calculated {len(specifications)} specifications in {calculation_time:.2f}s using {method}")
            
            return specifications, metrics
            
        except Exception as e:
            calculation_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"Calculation failed after {calculation_time:.2f}s: {e}")
            
            metrics = CalculationMetrics(
                total_elements=len(elements),
                processed_elements=0,
                calculation_time=calculation_time,
                method_used="failed",
                errors_encountered=len(elements)
            )
            
            return [], metrics
    
    def _elements_to_dataframe(self, elements: List[BuildingElement]) -> pd.DataFrame:
        """Convert building elements to DataFrame."""
        data = []
        for element in elements:
            data.append({
                'element_id': element.element_id,
                'project_id': element.project_id,
                'orientation': element.orientation.value if hasattr(element.orientation, 'value') else str(element.orientation),
                'azimuth': element.azimuth,
                'glass_area': element.glass_area,
                'pv_suitable': element.pv_suitable
            })
        return pd.DataFrame(data)
    
    def _radiation_to_dataframe(self, radiation_data: List[RadiationRecord]) -> pd.DataFrame:
        """Convert radiation records to DataFrame."""
        data = []
        for record in radiation_data:
            data.append({
                'element_id': record.element_id,
                'project_id': record.project_id,
                'annual_radiation': record.annual_radiation,
                'shading_factor': record.shading_factor
            })
        return pd.DataFrame(data)
    
    def _validate_input_data(self, elements_df: pd.DataFrame, radiation_df: pd.DataFrame) -> ValidationResult:
        """Validate input data quality."""
        errors = []
        warnings = []
        
        # Check for required columns
        required_element_cols = ['element_id', 'glass_area', 'orientation']
        required_radiation_cols = ['element_id', 'annual_radiation']
        
        missing_cols = [col for col in required_element_cols if col not in elements_df.columns]
        if missing_cols:
            errors.append(f"Missing element columns: {missing_cols}")
        
        missing_cols = [col for col in required_radiation_cols if col not in radiation_df.columns]
        if missing_cols:
            errors.append(f"Missing radiation columns: {missing_cols}")
        
        if errors:
            return ValidationResult(is_valid=False, errors=errors)
        
        # Validate value ranges
        invalid_areas = elements_df[elements_df['glass_area'] <= 0]
        if len(invalid_areas) > 0:
            errors.append(f"{len(invalid_areas)} elements with invalid glass area")
        
        invalid_radiation = radiation_df[
            (radiation_df['annual_radiation'] <= 0) | 
            (radiation_df['annual_radiation'] > VALIDATION_RANGES['annual_radiation'][1])
        ]
        if len(invalid_radiation) > 0:
            warnings.append(f"{len(invalid_radiation)} elements with questionable radiation values")
        
        # Check for matching element IDs
        element_ids = set(elements_df['element_id'])
        radiation_ids = set(radiation_df['element_id'])
        
        missing_radiation = element_ids - radiation_ids
        if missing_radiation:
            warnings.append(f"{len(missing_radiation)} elements missing radiation data")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            element_count=len(elements_df),
            radiation_count=len(radiation_df)
        )
    
    def _merge_element_radiation_data(self, elements_df: pd.DataFrame, radiation_df: pd.DataFrame) -> pd.DataFrame:
        """Merge element and radiation data."""
        merged = elements_df.merge(
            radiation_df[['element_id', 'annual_radiation', 'shading_factor']], 
            on='element_id', 
            how='inner'
        )
        
        # Filter suitable elements only
        merged = merged[merged['pv_suitable'] == True]
        
        # Apply orientation filtering if enabled
        if self.config.filter_by_orientation:
            unsuitable = self.config.unsuitable_orientations
            merged = merged[~merged['orientation'].isin(unsuitable)]
        
        # Apply minimum radiation threshold
        min_radiation = self.config.min_annual_radiation
        merged = merged[merged['annual_radiation'] >= min_radiation]
        
        return merged
    
    def _calculate_vectorized(
        self, 
        data: pd.DataFrame, 
        panel_spec: PanelSpecification,
        coverage_factor: float,
        performance_ratio: float
    ) -> List[ElementPVSpecification]:
        """Calculate specifications using vectorized pandas operations."""
        
        # Vectorized calculations
        data['effective_area'] = data['glass_area'] * coverage_factor
        data['system_power'] = (data['effective_area'] * panel_spec.power_density) / 1000  # kW
        
        # Apply orientation factors
        data['orientation_factor'] = data['orientation'].map(ORIENTATION_FACTORS).fillna(0.6)
        data['adjusted_radiation'] = data['annual_radiation'] * data['orientation_factor'] * data['shading_factor']
        
        # Energy calculations
        data['annual_energy'] = (
            data['system_power'] * 
            data['adjusted_radiation'] * 
            panel_spec.efficiency * 
            performance_ratio
        )
        
        # Specific yield
        data['specific_yield'] = np.where(
            data['system_power'] > 0,
            data['annual_energy'] / data['system_power'],
            0
        )
        
        # Cost calculations
        data['panel_cost'] = data['effective_area'] * panel_spec.cost_per_m2
        data['installation_cost'] = data['panel_cost'] * COST_PARAMETERS['installation_factor']
        data['inverter_cost'] = data['system_power'] * COST_PARAMETERS['inverter_cost_per_kw']
        data['structural_cost'] = data['glass_area'] * COST_PARAMETERS['structural_cost_per_m2']
        
        data['total_cost'] = (
            data['panel_cost'] + 
            data['installation_cost'] + 
            data['inverter_cost'] + 
            data['structural_cost'] + 
            COST_PARAMETERS['electrical_cost_per_system']
        ) * COST_PARAMETERS['margin_factor']
        
        # Cost per Wp
        data['system_power_wp'] = data['system_power'] * 1000
        data['cost_per_wp'] = np.where(
            data['system_power_wp'] > 0,
            data['total_cost'] / data['system_power_wp'],
            0
        )
        
        # Convert to specification objects
        specifications = []
        for _, row in data.iterrows():
            spec = ElementPVSpecification(
                project_id=int(row['project_id']),
                element_id=str(row['element_id']),
                panel_spec_id=panel_spec.id or 0,
                glass_area=float(row['glass_area']),
                panel_coverage=coverage_factor,
                effective_area=float(row['effective_area']),
                system_power=float(row['system_power']),
                annual_radiation=float(row['annual_radiation']),
                annual_energy=float(row['annual_energy']),
                specific_yield=float(row['specific_yield']),
                total_cost=float(row['total_cost']),
                cost_per_wp=float(row['cost_per_wp']),
                orientation=str(row['orientation'])
            )
            specifications.append(spec)
        
        return specifications
    
    def _calculate_with_dask(
        self, 
        data: pd.DataFrame, 
        panel_spec: PanelSpecification,
        coverage_factor: float,
        performance_ratio: float
    ) -> List[ElementPVSpecification]:
        """Calculate specifications using Dask for large datasets."""
        
        # Convert to Dask DataFrame
        ddf = dd.from_pandas(data, npartitions=4)
        
        # Vectorized calculations with Dask
        ddf['effective_area'] = ddf['glass_area'] * coverage_factor
        ddf['system_power'] = (ddf['effective_area'] * panel_spec.power_density) / 1000
        
        # Map orientation factors
        orientation_map = ORIENTATION_FACTORS
        ddf['orientation_factor'] = ddf['orientation'].map(orientation_map).fillna(0.6)
        ddf['adjusted_radiation'] = ddf['annual_radiation'] * ddf['orientation_factor'] * ddf['shading_factor']
        
        # Energy calculations
        ddf['annual_energy'] = (
            ddf['system_power'] * 
            ddf['adjusted_radiation'] * 
            panel_spec.efficiency * 
            performance_ratio
        )
        
        # Specific yield
        ddf['specific_yield'] = ddf['annual_energy'] / ddf['system_power'].where(ddf['system_power'] > 0, 1)
        
        # Cost calculations
        ddf['total_cost'] = (
            ddf['effective_area'] * panel_spec.cost_per_m2 * 
            COST_PARAMETERS['margin_factor']
        )
        
        ddf['cost_per_wp'] = ddf['total_cost'] / (ddf['system_power'] * 1000).where(ddf['system_power'] > 0, 1)
        
        # Compute results
        result_df = ddf.compute()
        
        # Convert to specification objects
        specifications = []
        for _, row in result_df.iterrows():
            spec = ElementPVSpecification(
                project_id=int(row['project_id']),
                element_id=str(row['element_id']),
                panel_spec_id=panel_spec.id or 0,
                glass_area=float(row['glass_area']),
                panel_coverage=coverage_factor,
                effective_area=float(row['effective_area']),
                system_power=float(row['system_power']),
                annual_radiation=float(row['annual_radiation']),
                annual_energy=float(row['annual_energy']),
                specific_yield=float(row['specific_yield']),
                total_cost=float(row['total_cost']),
                cost_per_wp=float(row['cost_per_wp']),
                orientation=str(row['orientation'])
            )
            specifications.append(spec)
        
        return specifications
    
    def _calculate_iterative(
        self, 
        data: pd.DataFrame, 
        panel_spec: PanelSpecification,
        coverage_factor: float,
        performance_ratio: float
    ) -> List[ElementPVSpecification]:
        """Calculate specifications iteratively (fallback method)."""
        
        specifications = []
        
        for _, row in data.iterrows():
            try:
                # Basic calculations
                effective_area = row['glass_area'] * coverage_factor
                system_power = (effective_area * panel_spec.power_density) / 1000  # kW
                
                # Apply orientation factor
                orientation_factor = ORIENTATION_FACTORS.get(row['orientation'], 0.6)
                adjusted_radiation = row['annual_radiation'] * orientation_factor * row.get('shading_factor', 1.0)
                
                # Energy calculation
                annual_energy = (
                    system_power * 
                    adjusted_radiation * 
                    panel_spec.efficiency * 
                    performance_ratio
                )
                
                # Specific yield
                specific_yield = annual_energy / system_power if system_power > 0 else 0
                
                # Cost calculation
                total_cost = (
                    effective_area * panel_spec.cost_per_m2 * 
                    COST_PARAMETERS['margin_factor']
                )
                
                # Cost per Wp
                system_power_wp = system_power * 1000
                cost_per_wp = total_cost / system_power_wp if system_power_wp > 0 else 0
                
                spec = ElementPVSpecification(
                    project_id=int(row['project_id']),
                    element_id=str(row['element_id']),
                    panel_spec_id=panel_spec.id or 0,
                    glass_area=float(row['glass_area']),
                    panel_coverage=coverage_factor,
                    effective_area=effective_area,
                    system_power=system_power,
                    annual_radiation=float(row['annual_radiation']),
                    annual_energy=annual_energy,
                    specific_yield=specific_yield,
                    total_cost=total_cost,
                    cost_per_wp=cost_per_wp,
                    orientation=str(row['orientation'])
                )
                
                specifications.append(spec)
                
            except Exception as e:
                logger.warning(f"Failed to calculate spec for element {row['element_id']}: {e}")
                continue
        
        return specifications
    
    def calculate_project_summary(self, specifications: List[ElementPVSpecification]) -> ProjectPVSummary:
        """Calculate project-level summary from specifications."""
        
        if not specifications:
            # Return empty summary
            return ProjectPVSummary(
                project_id=0,
                total_elements=0,
                suitable_elements=0,
                specified_elements=0,
                total_glass_area=0.0,
                total_effective_area=0.0,
                total_system_power=0.0,
                total_annual_energy=0.0,
                total_system_cost=0.0,
                avg_specific_yield=0.0,
                avg_cost_per_wp=0.0,
                orientation_breakdown={},
                power_breakdown={},
                cost_breakdown={},
                panel_type_distribution={},
                analysis_settings={}
            )
        
        # Convert to DataFrame for easy aggregation
        df = pd.DataFrame([spec.dict() for spec in specifications])
        
        # Calculate aggregations
        total_glass_area = df['glass_area'].sum()
        total_effective_area = df['effective_area'].sum()
        total_system_power = df['system_power'].sum()
        total_annual_energy = df['annual_energy'].sum()
        total_system_cost = df['total_cost'].sum()
        
        # Weighted averages
        avg_specific_yield = (
            (df['specific_yield'] * df['system_power']).sum() / total_system_power
            if total_system_power > 0 else 0
        )
        
        avg_cost_per_wp = (
            total_system_cost / (total_system_power * 1000)
            if total_system_power > 0 else 0
        )
        
        # Breakdowns by orientation
        orientation_breakdown = df['orientation'].value_counts().to_dict()
        power_breakdown = df.groupby('orientation')['system_power'].sum().to_dict()
        cost_breakdown = df.groupby('orientation')['total_cost'].sum().to_dict()
        
        # Panel type distribution (would need panel_spec info)
        panel_type_distribution = {"mixed": len(specifications)}
        
        return ProjectPVSummary(
            project_id=specifications[0].project_id,
            total_elements=len(specifications),
            suitable_elements=len(specifications),
            specified_elements=len(specifications),
            total_glass_area=total_glass_area,
            total_effective_area=total_effective_area,
            total_system_power=total_system_power,
            total_annual_energy=total_annual_energy,
            total_system_cost=total_system_cost,
            avg_specific_yield=avg_specific_yield,
            avg_cost_per_wp=avg_cost_per_wp,
            orientation_breakdown=orientation_breakdown,
            power_breakdown=power_breakdown,
            cost_breakdown=cost_breakdown,
            panel_type_distribution=panel_type_distribution,
            analysis_settings={
                "coverage_factor": specifications[0].panel_coverage,
                "calculation_method": "vectorized"
            }
        )
    
    @lru_cache(maxsize=128)
    def get_orientation_factor(self, orientation: str) -> float:
        """Get cached orientation factor."""
        return ORIENTATION_FACTORS.get(orientation, 0.6)
    
    def detect_unit_issues(self, data: pd.DataFrame) -> Dict[str, str]:
        """Detect potential unit conversion issues."""
        issues = {}
        
        if 'glass_area' in data.columns:
            max_area = data['glass_area'].max()
            if max_area > 1000:
                issues['glass_area'] = f"Maximum area {max_area} may be in cm² instead of m²"
        
        if 'annual_radiation' in data.columns:
            max_radiation = data['annual_radiation'].max()
            if max_radiation < 10:
                issues['annual_radiation'] = f"Values appear too low, may be in MWh/m² instead of kWh/m²"
        
        return issues
    
    def apply_unit_conversions(self, data: pd.DataFrame, conversions: Dict[str, str]) -> pd.DataFrame:
        """Apply unit conversions to data."""
        data_copy = data.copy()
        
        for column, conversion in conversions.items():
            if column in data_copy.columns:
                if conversion == "cm2_to_m2":
                    data_copy[column] = data_copy[column] * UNIT_CONVERSIONS['cm2_to_m2']
                elif conversion == "kwh_to_wh":
                    data_copy[column] = data_copy[column] * UNIT_CONVERSIONS['kwh_to_wh']
                elif conversion == "percent_to_decimal":
                    data_copy[column] = data_copy[column] * UNIT_CONVERSIONS['percent_to_decimal']
        
        return data_copy


# Global calculator instance
spec_calculator = SpecificationCalculator()