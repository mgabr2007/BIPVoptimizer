"""
Unit tests for BIPV panel catalog management.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from typing import List

from step6_pv_spec.models import PanelSpecification, PanelType
from step6_pv_spec.services.panel_catalog import PanelCatalogManager, get_default_panels


@pytest.fixture
def sample_panel():
    """Sample panel specification for testing."""
    return PanelSpecification(
        name="Test Panel BIPV",
        manufacturer="Test Manufacturer",
        panel_type=PanelType.SEMI_TRANSPARENT,
        efficiency=0.12,  # 12%
        transparency=0.25,  # 25%
        power_density=120.0,  # W/m²
        cost_per_m2=350.0,  # €/m²
        glass_thickness=8.0,
        u_value=1.8,
        glass_weight=27.0,
        performance_ratio=0.85
    )


@pytest.fixture
def catalog_manager():
    """Panel catalog manager instance."""
    return PanelCatalogManager()


class TestPanelCatalogManager:
    """Test cases for panel catalog manager."""
    
    @pytest.mark.asyncio
    async def test_add_panel_async(self, catalog_manager, sample_panel):
        """Test adding panel asynchronously."""
        with patch.object(catalog_manager.queries, 'insert_panel_async', 
                         return_value=1) as mock_insert:
            panel_id = await catalog_manager.add_panel_async(sample_panel)
            
            assert panel_id == 1
            mock_insert.assert_called_once_with(sample_panel)
    
    def test_add_panel_sync(self, catalog_manager, sample_panel):
        """Test adding panel synchronously."""
        with patch.object(catalog_manager.queries, 'insert_panel_sync', 
                         return_value=1) as mock_insert:
            panel_id = catalog_manager.add_panel_sync(sample_panel)
            
            assert panel_id == 1
            mock_insert.assert_called_once_with(sample_panel)
    
    @pytest.mark.asyncio
    async def test_get_all_panels_async(self, catalog_manager):
        """Test getting all panels asynchronously."""
        mock_panels = get_default_panels()
        
        with patch.object(catalog_manager.queries, 'get_all_active_panels_async', 
                         return_value=mock_panels) as mock_get:
            panels = await catalog_manager.get_all_panels_async()
            
            assert len(panels) == len(mock_panels)
            assert all(isinstance(panel, PanelSpecification) for panel in panels)
            mock_get.assert_called_once()
    
    def test_get_all_panels_sync(self, catalog_manager):
        """Test getting all panels synchronously."""
        mock_panels = get_default_panels()
        
        with patch.object(catalog_manager.queries, 'get_all_active_panels_sync', 
                         return_value=mock_panels) as mock_get:
            panels = catalog_manager.get_all_panels_sync()
            
            assert len(panels) == len(mock_panels)
            assert all(isinstance(panel, PanelSpecification) for panel in panels)
            mock_get.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_panels_by_type_async(self, catalog_manager):
        """Test filtering panels by type asynchronously."""
        mock_panels = [p for p in get_default_panels() if p.panel_type == PanelType.SEMI_TRANSPARENT]
        
        with patch.object(catalog_manager.queries, 'get_panels_by_type_async', 
                         return_value=mock_panels) as mock_get:
            panels = await catalog_manager.get_panels_by_type_async("semi_transparent")
            
            assert all(panel.panel_type == PanelType.SEMI_TRANSPARENT for panel in panels)
            mock_get.assert_called_once_with("semi_transparent")
    
    def test_search_panels(self, catalog_manager):
        """Test panel search functionality."""
        test_panels = get_default_panels()
        
        # Search by manufacturer
        results = catalog_manager.search_panels("Heliatek", test_panels)
        assert all("Heliatek" in panel.manufacturer for panel in results)
        
        # Search by name
        results = catalog_manager.search_panels("AVANCIS", test_panels)
        assert all("AVANCIS" in panel.manufacturer for panel in results)
        
        # Search by type
        results = catalog_manager.search_panels("semi_transparent", test_panels)
        assert all(panel.panel_type == PanelType.SEMI_TRANSPARENT for panel in results)
    
    def test_filter_panels_by_criteria(self, catalog_manager):
        """Test filtering panels by multiple criteria."""
        test_panels = get_default_panels()
        
        # Filter by efficiency range
        filtered = catalog_manager.filter_panels_by_criteria(
            test_panels,
            min_efficiency=0.10,
            max_efficiency=0.20
        )
        assert all(0.10 <= panel.efficiency <= 0.20 for panel in filtered)
        
        # Filter by cost
        filtered = catalog_manager.filter_panels_by_criteria(
            test_panels,
            max_cost=200.0
        )
        assert all(panel.cost_per_m2 <= 200.0 for panel in filtered)
        
        # Filter by panel type
        filtered = catalog_manager.filter_panels_by_criteria(
            test_panels,
            panel_types=["opaque"]
        )
        assert all(panel.panel_type == PanelType.OPAQUE for panel in filtered)
    
    def test_create_custom_panel(self, catalog_manager):
        """Test creating custom panel specification."""
        custom_panel = catalog_manager.create_custom_panel(
            name="Custom Test Panel",
            manufacturer="Custom Manufacturer",
            panel_type="semi_transparent",
            efficiency=0.14,
            transparency=0.30,
            cost_per_m2=400.0
        )
        
        assert custom_panel.name == "Custom Test Panel"
        assert custom_panel.manufacturer == "Custom Manufacturer"
        assert custom_panel.panel_type == "semi_transparent"
        assert custom_panel.efficiency == 0.14
        assert custom_panel.transparency == 0.30
        assert custom_panel.cost_per_m2 == 400.0
        assert custom_panel.power_density > 0  # Should be auto-calculated
    
    def test_panel_validation(self, catalog_manager, sample_panel):
        """Test panel specification validation."""
        # Valid panel should pass
        errors = catalog_manager._validate_panel_specification(sample_panel)
        assert len(errors) == 0
        
        # Invalid efficiency
        invalid_panel = sample_panel.copy()
        invalid_panel.efficiency = 2.0  # >100%
        
        with pytest.raises(ValueError):
            PanelSpecification(
                name="Invalid Panel",
                manufacturer="Test",
                panel_type=PanelType.OPAQUE,
                efficiency=2.0,  # Invalid
                transparency=0.0,
                power_density=150.0,
                cost_per_m2=300.0,
                glass_thickness=6.0,
                u_value=2.0,
                glass_weight=25.0
            )
    
    def test_power_density_calculation(self, catalog_manager):
        """Test auto-calculation of power density."""
        efficiency = 0.15  # 15%
        expected_power_density = efficiency * 1000  # Standard irradiance
        
        calculated_power_density = catalog_manager._calculate_power_density(efficiency)
        assert calculated_power_density == expected_power_density
    
    def test_panel_summary_stats(self, catalog_manager):
        """Test calculation of panel summary statistics."""
        test_panels = get_default_panels()
        
        stats = catalog_manager.get_panel_summary_stats(test_panels)
        
        assert stats['total_panels'] == len(test_panels)
        assert 'efficiency' in stats
        assert 'transparency' in stats
        assert 'cost' in stats
        assert 'manufacturers' in stats
        assert 'panel_types' in stats
        
        # Check efficiency stats
        efficiencies = [p.efficiency for p in test_panels]
        assert stats['efficiency']['min'] == min(efficiencies)
        assert stats['efficiency']['max'] == max(efficiencies)
        assert abs(stats['efficiency']['avg'] - sum(efficiencies) / len(efficiencies)) < 0.001
    
    @pytest.mark.asyncio
    async def test_catalog_initialization(self, catalog_manager):
        """Test catalog initialization with default panels."""
        # Mock empty catalog
        with patch.object(catalog_manager, 'get_all_panels_async', 
                         return_value=[]) as mock_get:
            with patch.object(catalog_manager, 'add_panel_async', 
                             return_value=1) as mock_add:
                
                success = await catalog_manager.initialize_catalog()
                
                assert success is True
                # Should have tried to add default panels
                assert mock_add.call_count > 0
    
    def test_export_import_catalog(self, catalog_manager):
        """Test catalog export and import functionality."""
        test_panels = get_default_panels()
        
        # Export to dict
        exported_data = catalog_manager.export_catalog_to_dict(test_panels)
        assert len(exported_data) == len(test_panels)
        assert all(isinstance(panel_dict, dict) for panel_dict in exported_data)
        
        # Import from dict
        imported_panels = catalog_manager.import_catalog_from_dict(exported_data)
        assert len(imported_panels) == len(test_panels)
        assert all(isinstance(panel, PanelSpecification) for panel in imported_panels)
        
        # Check data integrity
        for original, imported in zip(test_panels, imported_panels):
            assert original.name == imported.name
            assert original.manufacturer == imported.manufacturer
            assert original.efficiency == imported.efficiency


class TestDefaultPanels:
    """Test cases for default panel specifications."""
    
    def test_get_default_panels(self):
        """Test getting default panels."""
        panels = get_default_panels()
        
        assert len(panels) > 0
        assert all(isinstance(panel, PanelSpecification) for panel in panels)
        
        # Check that we have both opaque and semi-transparent panels
        panel_types = {panel.panel_type for panel in panels}
        assert PanelType.OPAQUE in panel_types
        assert PanelType.SEMI_TRANSPARENT in panel_types
    
    def test_default_panel_validity(self):
        """Test that all default panels are valid."""
        panels = get_default_panels()
        
        for panel in panels:
            # Check efficiency range
            assert 0.02 <= panel.efficiency <= 0.25
            
            # Check transparency range
            assert 0.0 <= panel.transparency <= 0.65
            
            # Check cost range
            assert 50.0 <= panel.cost_per_m2 <= 1000.0
            
            # Check power density
            assert 10.0 <= panel.power_density <= 250.0
            
            # Check names and manufacturers are not empty
            assert len(panel.name.strip()) > 0
            assert len(panel.manufacturer.strip()) > 0
    
    def test_panel_uniqueness(self):
        """Test that default panels have unique names."""
        panels = get_default_panels()
        
        names = [panel.name for panel in panels]
        assert len(names) == len(set(names))  # No duplicates
    
    def test_manufacturer_coverage(self):
        """Test that we have panels from multiple manufacturers."""
        panels = get_default_panels()
        
        manufacturers = {panel.manufacturer for panel in panels}
        assert len(manufacturers) >= 3  # At least 3 different manufacturers


@pytest.mark.integration
class TestCatalogIntegration:
    """Integration tests for catalog management."""
    
    @pytest.mark.asyncio
    async def test_full_catalog_workflow(self, catalog_manager, sample_panel):
        """Test complete catalog workflow: initialize, add, get, update, deactivate."""
        with patch.object(catalog_manager.queries, 'get_all_active_panels_async', 
                         return_value=[]) as mock_get:
            with patch.object(catalog_manager.queries, 'insert_panel_async', 
                             return_value=1) as mock_insert:
                with patch.object(catalog_manager.queries, 'update_panel_async', 
                                 return_value=True) as mock_update:
                    with patch.object(catalog_manager.queries, 'deactivate_panel_async', 
                                     return_value=True) as mock_deactivate:
                        
                        # Initialize catalog
                        await catalog_manager.initialize_catalog()
                        
                        # Add panel
                        panel_id = await catalog_manager.add_panel_async(sample_panel)
                        assert panel_id == 1
                        
                        # Update panel
                        sample_panel.id = panel_id
                        sample_panel.cost_per_m2 = 400.0  # Update cost
                        success = await catalog_manager.update_panel_async(sample_panel)
                        assert success is True
                        
                        # Deactivate panel
                        success = await catalog_manager.deactivate_panel_async(panel_id)
                        assert success is True


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])