"""
Async/sync parameterized SQL queries and database operations for PV specifications.
"""

import asyncio
import asyncpg
import psycopg2
import psycopg2.extras
from typing import List, Dict, Any, Optional, Union, Tuple
from contextlib import asynccontextmanager, contextmanager
import json
from datetime import datetime
import logging

from ..models import (
    PanelSpecification, ElementPVSpecification, BuildingElement, 
    RadiationRecord, ProjectPVSummary
)
from ..config import db_config, SQL_QUERIES, TABLE_NAMES

logger = logging.getLogger(__name__)


class DatabaseConnectionManager:
    """Enhanced database connection manager with async/sync support."""
    
    def __init__(self):
        self.config = db_config
        self._async_pool: Optional[asyncpg.Pool] = None
    
    @asynccontextmanager
    async def get_async_connection(self):
        """Get async database connection."""
        if self._async_pool is None:
            self._async_pool = await asyncpg.create_pool(
                host=self.config.host,
                port=self.config.port,
                user=self.config.username,
                password=self.config.password,
                database=self.config.database,
                min_size=self.config.min_connections,
                max_size=self.config.max_connections,
                timeout=self.config.connection_timeout
            )
        
        async with self._async_pool.acquire() as connection:
            yield connection
    
    @contextmanager
    def get_sync_connection(self):
        """Get synchronous database connection."""
        conn = None
        try:
            conn = psycopg2.connect(
                host=self.config.host,
                port=self.config.port,
                user=self.config.username,
                password=self.config.password,
                database=self.config.database
            )
            conn.autocommit = False
            yield conn
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Database connection error: {e}")
            raise
        finally:
            if conn:
                conn.close()
    
    async def close_pool(self):
        """Close async connection pool."""
        if self._async_pool:
            await self._async_pool.close()
            self._async_pool = None


class PanelCatalogQueries:
    """Database queries for panel catalog management."""
    
    def __init__(self):
        self.connection_manager = DatabaseConnectionManager()
    
    async def get_all_active_panels_async(self) -> List[PanelSpecification]:
        """Get all active panels asynchronously."""
        async with self.connection_manager.get_async_connection() as conn:
            rows = await conn.fetch(SQL_QUERIES["get_active_panels"])
            return [self._row_to_panel_spec(dict(row)) for row in rows]
    
    def get_all_active_panels_sync(self) -> List[PanelSpecification]:
        """Get all active panels synchronously."""
        with self.connection_manager.get_sync_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                cursor.execute(SQL_QUERIES["get_active_panels"])
                rows = cursor.fetchall()
                return [self._row_to_panel_spec(dict(row)) for row in rows]
    
    async def get_panels_by_type_async(self, panel_type: str) -> List[PanelSpecification]:
        """Get panels by type asynchronously."""
        async with self.connection_manager.get_async_connection() as conn:
            rows = await conn.fetch(SQL_QUERIES["get_panels_by_type"], panel_type)
            return [self._row_to_panel_spec(dict(row)) for row in rows]
    
    def get_panels_by_type_sync(self, panel_type: str) -> List[PanelSpecification]:
        """Get panels by type synchronously."""
        with self.connection_manager.get_sync_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                cursor.execute(SQL_QUERIES["get_panels_by_type"], (panel_type,))
                rows = cursor.fetchall()
                return [self._row_to_panel_spec(dict(row)) for row in rows]
    
    async def get_panel_by_id_async(self, panel_id: int) -> Optional[PanelSpecification]:
        """Get panel by ID asynchronously."""
        async with self.connection_manager.get_async_connection() as conn:
            row = await conn.fetchrow("SELECT * FROM panel_catalog WHERE id = $1", panel_id)
            return self._row_to_panel_spec(dict(row)) if row else None
    
    def get_panel_by_id_sync(self, panel_id: int) -> Optional[PanelSpecification]:
        """Get panel by ID synchronously."""
        with self.connection_manager.get_sync_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                cursor.execute("SELECT * FROM panel_catalog WHERE id = %s", (panel_id,))
                row = cursor.fetchone()
                return self._row_to_panel_spec(dict(row)) if row else None
    
    async def insert_panel_async(self, panel: PanelSpecification) -> int:
        """Insert new panel asynchronously."""
        async with self.connection_manager.get_async_connection() as conn:
            row = await conn.fetchrow(
                SQL_QUERIES["insert_panel"],
                panel.name, panel.manufacturer, panel.panel_type.value,
                panel.efficiency, panel.transparency, panel.power_density,
                panel.cost_per_m2, panel.glass_thickness, panel.u_value,
                panel.glass_weight, panel.performance_ratio, panel.is_active
            )
            return row['id'] if row else None
    
    def insert_panel_sync(self, panel: PanelSpecification) -> int:
        """Insert new panel synchronously."""
        with self.connection_manager.get_sync_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    SQL_QUERIES["insert_panel"],
                    (panel.name, panel.manufacturer, panel.panel_type.value,
                     panel.efficiency, panel.transparency, panel.power_density,
                     panel.cost_per_m2, panel.glass_thickness, panel.u_value,
                     panel.glass_weight, panel.performance_ratio, panel.is_active)
                )
                panel_id = cursor.fetchone()[0]
                conn.commit()
                return panel_id
    
    async def update_panel_async(self, panel: PanelSpecification) -> bool:
        """Update panel asynchronously."""
        async with self.connection_manager.get_async_connection() as conn:
            result = await conn.execute(
                SQL_QUERIES["update_panel"],
                panel.id, panel.name, panel.manufacturer, panel.panel_type.value,
                panel.efficiency, panel.transparency, panel.power_density,
                panel.cost_per_m2, panel.glass_thickness, panel.u_value,
                panel.glass_weight, panel.performance_ratio, panel.is_active
            )
            return "UPDATE 1" in result
    
    def update_panel_sync(self, panel: PanelSpecification) -> bool:
        """Update panel synchronously."""
        with self.connection_manager.get_sync_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    SQL_QUERIES["update_panel"],
                    (panel.id, panel.name, panel.manufacturer, panel.panel_type.value,
                     panel.efficiency, panel.transparency, panel.power_density,
                     panel.cost_per_m2, panel.glass_thickness, panel.u_value,
                     panel.glass_weight, panel.performance_ratio, panel.is_active)
                )
                success = cursor.rowcount > 0
                conn.commit()
                return success
    
    async def deactivate_panel_async(self, panel_id: int) -> bool:
        """Deactivate panel asynchronously."""
        async with self.connection_manager.get_async_connection() as conn:
            result = await conn.execute(
                "UPDATE panel_catalog SET is_active = false WHERE id = $1",
                panel_id
            )
            return "UPDATE 1" in result
    
    def deactivate_panel_sync(self, panel_id: int) -> bool:
        """Deactivate panel synchronously."""
        with self.connection_manager.get_sync_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "UPDATE panel_catalog SET is_active = false WHERE id = %s",
                    (panel_id,)
                )
                success = cursor.rowcount > 0
                conn.commit()
                return success
    
    def _row_to_panel_spec(self, row: Dict[str, Any]) -> PanelSpecification:
        """Convert database row to PanelSpecification object."""
        return PanelSpecification(
            id=row['id'],
            name=row['name'],
            manufacturer=row['manufacturer'],
            panel_type=row['panel_type'],
            efficiency=float(row['efficiency']),
            transparency=float(row['transparency']),
            power_density=float(row['power_density']),
            cost_per_m2=float(row['cost_per_m2']),
            glass_thickness=float(row['glass_thickness']),
            u_value=float(row['u_value']),
            glass_weight=float(row['glass_weight']),
            performance_ratio=float(row['performance_ratio']),
            is_active=bool(row['is_active']),
            created_at=row.get('created_at', datetime.now()),
            updated_at=row.get('updated_at', datetime.now())
        )


class SpecificationQueries:
    """Database queries for PV specifications management."""
    
    def __init__(self):
        self.connection_manager = DatabaseConnectionManager()
    
    async def get_building_elements_with_radiation_async(self, project_id: int) -> List[Dict[str, Any]]:
        """Get building elements with radiation data asynchronously."""
        async with self.connection_manager.get_async_connection() as conn:
            rows = await conn.fetch(SQL_QUERIES["get_building_elements_with_radiation"], project_id)
            return [dict(row) for row in rows]
    
    def get_building_elements_with_radiation_sync(self, project_id: int) -> List[Dict[str, Any]]:
        """Get building elements with radiation data synchronously."""
        with self.connection_manager.get_sync_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                cursor.execute(SQL_QUERIES["get_building_elements_with_radiation"], (project_id,))
                return [dict(row) for row in cursor.fetchall()]
    
    async def bulk_upsert_specifications_async(self, specifications: List[ElementPVSpecification]) -> int:
        """Bulk upsert specifications asynchronously."""
        if not specifications:
            return 0
        
        async with self.connection_manager.get_async_connection() as conn:
            # Prepare data for bulk insert
            values = []
            for spec in specifications:
                values.append((
                    spec.project_id, spec.element_id, spec.panel_spec_id,
                    spec.glass_area, spec.panel_coverage, spec.effective_area,
                    spec.system_power, spec.annual_radiation, spec.annual_energy,
                    spec.specific_yield, spec.total_cost, spec.cost_per_wp,
                    spec.orientation, spec.created_at
                ))
            
            # Use copy_records_to_table for high performance
            await conn.copy_records_to_table(
                'element_pv_specifications_temp', 
                records=values,
                columns=[
                    'project_id', 'element_id', 'panel_spec_id', 'glass_area',
                    'panel_coverage', 'effective_area', 'system_power',
                    'annual_radiation', 'annual_energy', 'specific_yield',
                    'total_cost', 'cost_per_wp', 'orientation', 'created_at'
                ]
            )
            
            # Upsert from temp table
            await conn.execute("""
                INSERT INTO element_pv_specifications 
                SELECT * FROM element_pv_specifications_temp
                ON CONFLICT (project_id, element_id) 
                DO UPDATE SET
                    panel_spec_id = EXCLUDED.panel_spec_id,
                    glass_area = EXCLUDED.glass_area,
                    panel_coverage = EXCLUDED.panel_coverage,
                    effective_area = EXCLUDED.effective_area,
                    system_power = EXCLUDED.system_power,
                    annual_radiation = EXCLUDED.annual_radiation,
                    annual_energy = EXCLUDED.annual_energy,
                    specific_yield = EXCLUDED.specific_yield,
                    total_cost = EXCLUDED.total_cost,
                    cost_per_wp = EXCLUDED.cost_per_wp,
                    orientation = EXCLUDED.orientation,
                    created_at = EXCLUDED.created_at
            """)
            
            # Clear temp table
            await conn.execute("TRUNCATE element_pv_specifications_temp")
            
            return len(specifications)
    
    def bulk_upsert_specifications_sync(self, specifications: List[ElementPVSpecification]) -> int:
        """Bulk upsert specifications synchronously."""
        if not specifications:
            return 0
        
        with self.connection_manager.get_sync_connection() as conn:
            with conn.cursor() as cursor:
                # Prepare data for bulk insert
                values = []
                for spec in specifications:
                    values.append((
                        spec.project_id, spec.element_id, spec.panel_spec_id,
                        spec.glass_area, spec.panel_coverage, spec.effective_area,
                        spec.system_power, spec.annual_radiation, spec.annual_energy,
                        spec.specific_yield, spec.total_cost, spec.cost_per_wp,
                        spec.orientation, spec.created_at
                    ))
                
                # Use execute_values for bulk insert
                psycopg2.extras.execute_values(
                    cursor,
                    SQL_QUERIES["upsert_element_specification"],
                    values,
                    template=None,
                    page_size=self.connection_manager.config.batch_size
                )
                
                conn.commit()
                return len(specifications)
    
    async def get_project_specifications_async(self, project_id: int) -> List[ElementPVSpecification]:
        """Get project specifications asynchronously."""
        async with self.connection_manager.get_async_connection() as conn:
            rows = await conn.fetch(SQL_QUERIES["get_project_specifications"], project_id)
            return [self._row_to_element_spec(dict(row)) for row in rows]
    
    def get_project_specifications_sync(self, project_id: int) -> List[ElementPVSpecification]:
        """Get project specifications synchronously."""
        with self.connection_manager.get_sync_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                cursor.execute(SQL_QUERIES["get_project_specifications"], (project_id,))
                rows = cursor.fetchall()
                return [self._row_to_element_spec(dict(row)) for row in rows]
    
    async def get_specification_summary_async(self, project_id: int) -> Optional[Dict[str, Any]]:
        """Get specification summary asynchronously."""
        async with self.connection_manager.get_async_connection() as conn:
            row = await conn.fetchrow(SQL_QUERIES["get_specification_summary"], project_id)
            return dict(row) if row else None
    
    def get_specification_summary_sync(self, project_id: int) -> Optional[Dict[str, Any]]:
        """Get specification summary synchronously."""
        with self.connection_manager.get_sync_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                cursor.execute(SQL_QUERIES["get_specification_summary"], (project_id,))
                row = cursor.fetchone()
                return dict(row) if row else None
    
    async def clear_project_specifications_async(self, project_id: int) -> int:
        """Clear project specifications asynchronously."""
        async with self.connection_manager.get_async_connection() as conn:
            result = await conn.execute(SQL_QUERIES["clear_project_specifications"], project_id)
            # Extract row count from result
            return int(result.split()[-1]) if "DELETE" in result else 0
    
    def clear_project_specifications_sync(self, project_id: int) -> int:
        """Clear project specifications synchronously."""
        with self.connection_manager.get_sync_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(SQL_QUERIES["clear_project_specifications"], (project_id,))
                count = cursor.rowcount
                conn.commit()
                return count
    
    def _row_to_element_spec(self, row: Dict[str, Any]) -> ElementPVSpecification:
        """Convert database row to ElementPVSpecification object."""
        return ElementPVSpecification(
            id=row.get('id'),
            project_id=int(row['project_id']),
            element_id=str(row['element_id']),
            panel_spec_id=int(row['panel_spec_id']),
            glass_area=float(row['glass_area']),
            panel_coverage=float(row['panel_coverage']),
            effective_area=float(row['effective_area']),
            system_power=float(row['system_power']),
            annual_radiation=float(row['annual_radiation']),
            annual_energy=float(row['annual_energy']),
            specific_yield=float(row['specific_yield']),
            total_cost=float(row['total_cost']),
            cost_per_wp=float(row['cost_per_wp']),
            orientation=str(row['orientation']),
            created_at=row.get('created_at', datetime.now())
        )


class ProjectDataQueries:
    """Database queries for project-level data aggregation."""
    
    def __init__(self):
        self.connection_manager = DatabaseConnectionManager()
    
    async def get_orientation_breakdown_async(self, project_id: int) -> Dict[str, Any]:
        """Get orientation breakdown asynchronously."""
        async with self.connection_manager.get_async_connection() as conn:
            rows = await conn.fetch("""
                SELECT orientation, 
                       COUNT(*) as element_count,
                       SUM(system_power) as total_power,
                       SUM(total_cost) as total_cost,
                       AVG(specific_yield) as avg_specific_yield
                FROM element_pv_specifications 
                WHERE project_id = $1 
                GROUP BY orientation
                ORDER BY total_power DESC
            """, project_id)
            
            return {
                'counts': {row['orientation']: row['element_count'] for row in rows},
                'power': {row['orientation']: float(row['total_power']) for row in rows},
                'cost': {row['orientation']: float(row['total_cost']) for row in rows},
                'yield': {row['orientation']: float(row['avg_specific_yield']) for row in rows}
            }
    
    def get_orientation_breakdown_sync(self, project_id: int) -> Dict[str, Any]:
        """Get orientation breakdown synchronously."""
        with self.connection_manager.get_sync_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT orientation, 
                           COUNT(*) as element_count,
                           SUM(system_power) as total_power,
                           SUM(total_cost) as total_cost,
                           AVG(specific_yield) as avg_specific_yield
                    FROM element_pv_specifications 
                    WHERE project_id = %s 
                    GROUP BY orientation
                    ORDER BY total_power DESC
                """, (project_id,))
                
                rows = cursor.fetchall()
                
                return {
                    'counts': {row['orientation']: row['element_count'] for row in rows},
                    'power': {row['orientation']: float(row['total_power']) for row in rows},
                    'cost': {row['orientation']: float(row['total_cost']) for row in rows},
                    'yield': {row['orientation']: float(row['avg_specific_yield']) for row in rows}
                }


# Global query instances
panel_catalog_queries = PanelCatalogQueries()
specification_queries = SpecificationQueries()
project_data_queries = ProjectDataQueries()


async def execute_with_fallback(async_func, sync_func, *args, **kwargs):
    """Execute async function with sync fallback."""
    try:
        # Try async first
        return await async_func(*args, **kwargs)
    except Exception as e:
        logger.warning(f"Async execution failed, falling back to sync: {e}")
        # Fallback to sync
        return sync_func(*args, **kwargs)


def create_temp_tables():
    """Create temporary tables for bulk operations."""
    temp_table_sql = """
        CREATE TEMP TABLE IF NOT EXISTS element_pv_specifications_temp (
            LIKE element_pv_specifications INCLUDING ALL
        );
    """
    
    try:
        with panel_catalog_queries.connection_manager.get_sync_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(temp_table_sql)
                conn.commit()
    except Exception as e:
        logger.warning(f"Failed to create temp tables: {e}")


def ensure_indexes():
    """Ensure all required indexes exist."""
    from ..config import INDEX_STATEMENTS
    
    try:
        with panel_catalog_queries.connection_manager.get_sync_connection() as conn:
            with conn.cursor() as cursor:
                for index_sql in INDEX_STATEMENTS:
                    cursor.execute(index_sql)
                conn.commit()
                logger.info("All database indexes ensured")
    except Exception as e:
        logger.error(f"Failed to ensure indexes: {e}")


# Initialize temp tables and indexes on module import
create_temp_tables()
ensure_indexes()