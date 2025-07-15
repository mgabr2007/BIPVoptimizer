"""
BIPV panel catalog management with CRUD operations and database persistence.
"""

import asyncio
from typing import List, Dict, Any, Optional
from functools import lru_cache
import logging
from datetime import datetime

from ..models import PanelSpecification, DEFAULT_PANEL_SPECIFICATIONS
from ..config import catalog_config, VALIDATION_RANGES
from ..db.queries import panel_catalog_queries

logger = logging.getLogger(__name__)


class PanelCatalogManager:
    """Manages BIPV panel catalog with database persistence and caching."""
    
    def __init__(self):
        self.config = catalog_config
        self.queries = panel_catalog_queries
        self._cache_enabled = self.config.enable_catalog_cache
        self._initialized = False
    
    async def initialize_catalog(self) -> bool:
        """Initialize catalog with default panel specifications."""
        try:
            # Check if catalog is already populated
            existing_panels = await self.get_all_panels_async()
            
            if len(existing_panels) > 0:
                logger.info(f"Catalog already contains {len(existing_panels)} panels")
                self._initialized = True
                return True
            
            # Insert default panels
            inserted_count = 0
            for panel_data in DEFAULT_PANEL_SPECIFICATIONS:
                try:
                    panel = PanelSpecification(**panel_data)
                    await self.add_panel_async(panel)
                    inserted_count += 1
                except Exception as e:
                    logger.warning(f"Failed to insert default panel {panel_data.get('name')}: {e}")
            
            logger.info(f"Initialized catalog with {inserted_count} default panels")
            self._initialized = True
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize catalog: {e}")
            return False
    
    async def get_all_panels_async(self) -> List[PanelSpecification]:
        """Get all active panels from catalog."""
        try:
            if self._cache_enabled:
                return await self._get_panels_cached_async()
            else:
                return await self.queries.get_all_active_panels_async()
        except Exception as e:
            logger.error(f"Failed to get panels: {e}")
            return []
    
    def get_all_panels_sync(self) -> List[PanelSpecification]:
        """Get all active panels synchronously."""
        try:
            return self.queries.get_all_active_panels_sync()
        except Exception as e:
            logger.error(f"Failed to get panels: {e}")
            return []
    
    async def get_panels_by_type_async(self, panel_type: str) -> List[PanelSpecification]:
        """Get panels filtered by type."""
        try:
            return await self.queries.get_panels_by_type_async(panel_type)
        except Exception as e:
            logger.error(f"Failed to get panels by type {panel_type}: {e}")
            return []
    
    def get_panels_by_type_sync(self, panel_type: str) -> List[PanelSpecification]:
        """Get panels filtered by type synchronously."""
        try:
            return self.queries.get_panels_by_type_sync(panel_type)
        except Exception as e:
            logger.error(f"Failed to get panels by type {panel_type}: {e}")
            return []
    
    async def get_panel_by_id_async(self, panel_id: int) -> Optional[PanelSpecification]:
        """Get specific panel by ID."""
        try:
            return await self.queries.get_panel_by_id_async(panel_id)
        except Exception as e:
            logger.error(f"Failed to get panel {panel_id}: {e}")
            return None
    
    def get_panel_by_id_sync(self, panel_id: int) -> Optional[PanelSpecification]:
        """Get specific panel by ID synchronously."""
        try:
            return self.queries.get_panel_by_id_sync(panel_id)
        except Exception as e:
            logger.error(f"Failed to get panel {panel_id}: {e}")
            return None
    
    async def add_panel_async(self, panel: PanelSpecification) -> Optional[int]:
        """Add new panel to catalog."""
        try:
            # Validate panel specification
            validation_errors = self._validate_panel_specification(panel)
            if validation_errors:
                raise ValueError(f"Panel validation failed: {validation_errors}")
            
            # Auto-calculate power density if missing
            if self.config.auto_calculate_power_density and panel.power_density == 0:
                panel.power_density = self._calculate_power_density(panel.efficiency)
            
            panel_id = await self.queries.insert_panel_async(panel)
            
            # Clear cache if enabled
            if self._cache_enabled:
                self._clear_cache()
            
            logger.info(f"Added panel '{panel.name}' with ID {panel_id}")
            return panel_id
            
        except Exception as e:
            logger.error(f"Failed to add panel '{panel.name}': {e}")
            return None
    
    def add_panel_sync(self, panel: PanelSpecification) -> Optional[int]:
        """Add new panel to catalog synchronously."""
        try:
            # Validate panel specification
            validation_errors = self._validate_panel_specification(panel)
            if validation_errors:
                raise ValueError(f"Panel validation failed: {validation_errors}")
            
            # Auto-calculate power density if missing
            if self.config.auto_calculate_power_density and panel.power_density == 0:
                panel.power_density = self._calculate_power_density(panel.efficiency)
            
            panel_id = self.queries.insert_panel_sync(panel)
            
            # Clear cache if enabled
            if self._cache_enabled:
                self._clear_cache()
            
            logger.info(f"Added panel '{panel.name}' with ID {panel_id}")
            return panel_id
            
        except Exception as e:
            logger.error(f"Failed to add panel '{panel.name}': {e}")
            return None
    
    async def update_panel_async(self, panel: PanelSpecification) -> bool:
        """Update existing panel in catalog."""
        try:
            if not panel.id:
                raise ValueError("Panel ID is required for update")
            
            # Validate panel specification
            validation_errors = self._validate_panel_specification(panel)
            if validation_errors:
                raise ValueError(f"Panel validation failed: {validation_errors}")
            
            # Auto-calculate power density if missing
            if self.config.auto_calculate_power_density and panel.power_density == 0:
                panel.power_density = self._calculate_power_density(panel.efficiency)
            
            success = await self.queries.update_panel_async(panel)
            
            # Clear cache if enabled
            if self._cache_enabled:
                self._clear_cache()
            
            if success:
                logger.info(f"Updated panel '{panel.name}' (ID: {panel.id})")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to update panel '{panel.name}': {e}")
            return False
    
    def update_panel_sync(self, panel: PanelSpecification) -> bool:
        """Update existing panel in catalog synchronously."""
        try:
            if not panel.id:
                raise ValueError("Panel ID is required for update")
            
            # Validate panel specification
            validation_errors = self._validate_panel_specification(panel)
            if validation_errors:
                raise ValueError(f"Panel validation failed: {validation_errors}")
            
            # Auto-calculate power density if missing
            if self.config.auto_calculate_power_density and panel.power_density == 0:
                panel.power_density = self._calculate_power_density(panel.efficiency)
            
            success = self.queries.update_panel_sync(panel)
            
            # Clear cache if enabled
            if self._cache_enabled:
                self._clear_cache()
            
            if success:
                logger.info(f"Updated panel '{panel.name}' (ID: {panel.id})")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to update panel '{panel.name}': {e}")
            return False
    
    async def deactivate_panel_async(self, panel_id: int) -> bool:
        """Deactivate panel (soft delete)."""
        try:
            success = await self.queries.deactivate_panel_async(panel_id)
            
            # Clear cache if enabled
            if self._cache_enabled:
                self._clear_cache()
            
            if success:
                logger.info(f"Deactivated panel ID {panel_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to deactivate panel {panel_id}: {e}")
            return False
    
    def deactivate_panel_sync(self, panel_id: int) -> bool:
        """Deactivate panel synchronously."""
        try:
            success = self.queries.deactivate_panel_sync(panel_id)
            
            # Clear cache if enabled
            if self._cache_enabled:
                self._clear_cache()
            
            if success:
                logger.info(f"Deactivated panel ID {panel_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to deactivate panel {panel_id}: {e}")
            return False
    
    def create_custom_panel(
        self,
        name: str,
        manufacturer: str,
        panel_type: str,
        efficiency: float,
        transparency: float,
        cost_per_m2: float,
        **kwargs
    ) -> PanelSpecification:
        """Create custom panel specification with validation."""
        
        # Auto-calculate power density if not provided
        power_density = kwargs.get('power_density')
        if not power_density and self.config.auto_calculate_power_density:
            power_density = self._calculate_power_density(efficiency)
        
        # Set defaults for optional parameters
        panel_data = {
            'name': name,
            'manufacturer': manufacturer,
            'panel_type': panel_type,
            'efficiency': efficiency,
            'transparency': transparency,
            'power_density': power_density or 100.0,
            'cost_per_m2': cost_per_m2,
            'glass_thickness': kwargs.get('glass_thickness', 6.0),
            'u_value': kwargs.get('u_value', 2.0),
            'glass_weight': kwargs.get('glass_weight', 25.0),
            'performance_ratio': kwargs.get('performance_ratio', 0.85),
            'is_active': True
        }
        
        return PanelSpecification(**panel_data)
    
    def search_panels(self, query: str, panels: List[PanelSpecification]) -> List[PanelSpecification]:
        """Search panels by name, manufacturer, or type."""
        query_lower = query.lower()
        
        matching_panels = []
        for panel in panels:
            if (query_lower in panel.name.lower() or 
                query_lower in panel.manufacturer.lower() or
                query_lower in panel.panel_type.lower()):
                matching_panels.append(panel)
        
        return matching_panels
    
    def filter_panels_by_criteria(
        self,
        panels: List[PanelSpecification],
        min_efficiency: Optional[float] = None,
        max_efficiency: Optional[float] = None,
        min_transparency: Optional[float] = None,
        max_transparency: Optional[float] = None,
        max_cost: Optional[float] = None,
        panel_types: Optional[List[str]] = None
    ) -> List[PanelSpecification]:
        """Filter panels by multiple criteria."""
        
        filtered_panels = panels.copy()
        
        if min_efficiency is not None:
            filtered_panels = [p for p in filtered_panels if p.efficiency >= min_efficiency]
        
        if max_efficiency is not None:
            filtered_panels = [p for p in filtered_panels if p.efficiency <= max_efficiency]
        
        if min_transparency is not None:
            filtered_panels = [p for p in filtered_panels if p.transparency >= min_transparency]
        
        if max_transparency is not None:
            filtered_panels = [p for p in filtered_panels if p.transparency <= max_transparency]
        
        if max_cost is not None:
            filtered_panels = [p for p in filtered_panels if p.cost_per_m2 <= max_cost]
        
        if panel_types:
            filtered_panels = [p for p in filtered_panels if p.panel_type in panel_types]
        
        return filtered_panels
    
    def get_panel_summary_stats(self, panels: List[PanelSpecification]) -> Dict[str, Any]:
        """Get summary statistics for panel collection."""
        if not panels:
            return {}
        
        efficiencies = [p.efficiency for p in panels]
        transparencies = [p.transparency for p in panels]
        costs = [p.cost_per_m2 for p in panels]
        
        return {
            'total_panels': len(panels),
            'efficiency': {
                'min': min(efficiencies),
                'max': max(efficiencies),
                'avg': sum(efficiencies) / len(efficiencies)
            },
            'transparency': {
                'min': min(transparencies),
                'max': max(transparencies),
                'avg': sum(transparencies) / len(transparencies)
            },
            'cost': {
                'min': min(costs),
                'max': max(costs),
                'avg': sum(costs) / len(costs)
            },
            'manufacturers': len(set(p.manufacturer for p in panels)),
            'panel_types': {ptype: sum(1 for p in panels if p.panel_type == ptype) 
                          for ptype in set(p.panel_type for p in panels)}
        }
    
    def _validate_panel_specification(self, panel: PanelSpecification) -> List[str]:
        """Validate panel specification against ranges."""
        errors = []
        
        # Check efficiency range
        eff_min, eff_max = VALIDATION_RANGES['efficiency']
        if not eff_min <= panel.efficiency <= eff_max:
            errors.append(f"Efficiency {panel.efficiency:.1%} outside valid range ({eff_min:.1%}-{eff_max:.1%})")
        
        # Check transparency range
        trans_min, trans_max = VALIDATION_RANGES['transparency']
        if not trans_min <= panel.transparency <= trans_max:
            errors.append(f"Transparency {panel.transparency:.1%} outside valid range ({trans_min:.1%}-{trans_max:.1%})")
        
        # Check power density range
        power_min, power_max = VALIDATION_RANGES['power_density']
        if not power_min <= panel.power_density <= power_max:
            errors.append(f"Power density {panel.power_density} W/m² outside valid range ({power_min}-{power_max})")
        
        # Check cost range
        cost_min, cost_max = VALIDATION_RANGES['cost_per_m2']
        if not cost_min <= panel.cost_per_m2 <= cost_max:
            errors.append(f"Cost €{panel.cost_per_m2}/m² outside valid range (€{cost_min}-€{cost_max})")
        
        # Check name uniqueness (would need database query in real implementation)
        if not panel.name or len(panel.name.strip()) < 3:
            errors.append("Panel name must be at least 3 characters")
        
        if not panel.manufacturer or len(panel.manufacturer.strip()) < 2:
            errors.append("Manufacturer name must be at least 2 characters")
        
        return errors
    
    def _calculate_power_density(self, efficiency: float) -> float:
        """Auto-calculate power density from efficiency."""
        # Assume standard test conditions (1000 W/m²)
        return efficiency * self.config.standard_irradiance
    
    @lru_cache(maxsize=1)
    async def _get_panels_cached_async(self) -> List[PanelSpecification]:
        """Get panels with LRU caching."""
        return await self.queries.get_all_active_panels_async()
    
    def _clear_cache(self):
        """Clear LRU cache."""
        if hasattr(self, '_get_panels_cached_async'):
            self._get_panels_cached_async.cache_clear()
    
    def export_catalog_to_dict(self, panels: List[PanelSpecification]) -> List[Dict[str, Any]]:
        """Export catalog to dictionary format."""
        return [panel.dict(exclude={'id', 'created_at', 'updated_at'}) for panel in panels]
    
    def import_catalog_from_dict(self, catalog_data: List[Dict[str, Any]]) -> List[PanelSpecification]:
        """Import catalog from dictionary format."""
        panels = []
        for panel_data in catalog_data:
            try:
                panel = PanelSpecification(**panel_data)
                panels.append(panel)
            except Exception as e:
                logger.warning(f"Failed to import panel {panel_data.get('name', 'unknown')}: {e}")
        
        return panels


# Global catalog manager instance
panel_catalog_manager = PanelCatalogManager()


def get_default_panels() -> List[PanelSpecification]:
    """Get default panel specifications as objects."""
    panels = []
    for panel_data in DEFAULT_PANEL_SPECIFICATIONS:
        try:
            panel = PanelSpecification(**panel_data)
            panels.append(panel)
        except Exception as e:
            logger.warning(f"Failed to create default panel {panel_data.get('name')}: {e}")
    
    return panels


async def ensure_catalog_initialized():
    """Ensure catalog is initialized with default panels."""
    if not panel_catalog_manager._initialized:
        await panel_catalog_manager.initialize_catalog()


def get_panel_by_name(name: str, panels: List[PanelSpecification]) -> Optional[PanelSpecification]:
    """Find panel by exact name match."""
    for panel in panels:
        if panel.name == name:
            return panel
    return None


def get_recommended_panels_for_application(application: str) -> List[str]:
    """Get recommended panel types for specific application."""
    recommendations = {
        'windows': ['semi_transparent'],
        'facades': ['opaque', 'semi_transparent'],
        'skylights': ['semi_transparent'],
        'curtain_walls': ['semi_transparent'],
        'canopies': ['opaque'],
        'roofs': ['opaque']
    }
    
    return recommendations.get(application.lower(), ['opaque', 'semi_transparent'])