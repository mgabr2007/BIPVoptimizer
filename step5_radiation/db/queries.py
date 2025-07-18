"""
Parameterized SQL queries and asyncpg helpers for radiation analysis.
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
from ..config import db_config, SQL_QUERIES, TABLE_NAMES
from ..models import ElementRadiationResult, ProjectRadiationSummary, DatabaseMetrics

logger = logging.getLogger(__name__)


class DatabaseConnectionManager:
    """Enhanced database connection manager with async support."""
    
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


class RadiationDataQueries:
    """Optimized queries for radiation analysis data operations."""
    
    def __init__(self):
        self.connection_manager = DatabaseConnectionManager()
        self.config = db_config  # Add missing config reference
    
    async def get_suitable_elements_async(self, project_id: int) -> List[Dict[str, Any]]:
        """Get PV-suitable building elements asynchronously."""
        async with self.connection_manager.get_async_connection() as conn:
            query = SQL_QUERIES["get_project_elements"]
            rows = await conn.fetch(query, project_id)
            return [dict(row) for row in rows]
    
    def get_suitable_elements_sync(self, project_id: int) -> List[Dict[str, Any]]:
        """Get PV-suitable building elements synchronously."""
        with self.connection_manager.get_sync_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                cursor.execute(SQL_QUERIES["get_project_elements"], (project_id,))
                return [dict(row) for row in cursor.fetchall()]
    
    async def get_wall_data_async(self, project_id: int) -> List[Dict[str, Any]]:
        """Get wall geometry data asynchronously."""
        async with self.connection_manager.get_async_connection() as conn:
            query = SQL_QUERIES["get_wall_data"]
            rows = await conn.fetch(query, project_id)
            return [dict(row) for row in rows]
    
    def get_wall_data_sync(self, project_id: int) -> List[Dict[str, Any]]:
        """Get wall geometry data synchronously."""
        with self.connection_manager.get_sync_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                cursor.execute(SQL_QUERIES["get_wall_data"], (project_id,))
                return [dict(row) for row in cursor.fetchall()]
    
    async def bulk_upsert_radiation_results_async(self, results: List[ElementRadiationResult]) -> DatabaseMetrics:
        """Bulk upsert radiation results asynchronously."""
        start_time = datetime.now()
        rows_affected = 0
        
        try:
            async with self.connection_manager.get_async_connection() as conn:
                # Prepare data for bulk insert - match actual database schema
                values = [
                    (
                        r.project_id, r.element_id, r.annual_radiation,
                        getattr(r, 'irradiance', 0.0), getattr(r, 'orientation_multiplier', 1.0),
                        getattr(r, 'calculation_method', 'advanced'), r.calculated_at
                    )
                    for r in results
                ]
                
                # Execute bulk upsert
                query = SQL_QUERIES["upsert_radiation_result"]
                await conn.executemany(query, values)
                rows_affected = len(values)
                
                execution_time = (datetime.now() - start_time).total_seconds()
                
                return DatabaseMetrics(
                    operation="bulk_upsert_radiation",
                    table_name="element_radiation",
                    rows_affected=rows_affected,
                    execution_time=execution_time,
                    success=True
                )
                
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"Bulk upsert failed: {e}")
            return DatabaseMetrics(
                operation="bulk_upsert_radiation",
                table_name="element_radiation",
                rows_affected=0,
                execution_time=execution_time,
                success=False,
                error_message=str(e)
            )
    
    def bulk_upsert_radiation_results_sync(self, results: List[ElementRadiationResult]) -> DatabaseMetrics:
        """Bulk upsert radiation results synchronously."""
        start_time = datetime.now()
        rows_affected = 0
        
        try:
            with self.connection_manager.get_sync_connection() as conn:
                with conn.cursor() as cursor:
                    # Prepare data for bulk insert - match actual database schema
                    values = [
                        (
                            r.project_id, r.element_id, r.annual_radiation,
                            getattr(r, 'irradiance', 0.0), getattr(r, 'orientation_multiplier', 1.0),
                            getattr(r, 'calculation_method', 'advanced'), r.calculated_at
                        )
                        for r in results
                    ]
                    
                    # Execute bulk upsert using execute_values
                    query = SQL_QUERIES["upsert_radiation_result"]
                    psycopg2.extras.execute_values(
                        cursor, query, values,
                        template=None, page_size=self.config.batch_size
                    )
                    
                    rows_affected = cursor.rowcount
                    conn.commit()
                    
                    execution_time = (datetime.now() - start_time).total_seconds()
                    
                    return DatabaseMetrics(
                        operation="bulk_upsert_radiation",
                        table_name="element_radiation",
                        rows_affected=rows_affected,
                        execution_time=execution_time,
                        success=True
                    )
                    
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"Bulk upsert failed: {e}")
            return DatabaseMetrics(
                operation="bulk_upsert_radiation",
                table_name="element_radiation",
                rows_affected=0,
                execution_time=execution_time,
                success=False,
                error_message=str(e)
            )
    
    async def get_radiation_summary_async(self, project_id: int) -> Optional[ProjectRadiationSummary]:
        """Get radiation analysis summary asynchronously."""
        try:
            async with self.connection_manager.get_async_connection() as conn:
                query = SQL_QUERIES["get_radiation_summary"]
                rows = await conn.fetch(query, project_id)
                
                if not rows:
                    return None
                
                # Aggregate results
                total_elements = sum(row['orientation_count'] for row in rows)
                total_area = sum(row['total_area'] for row in rows if row['total_area'])
                avg_radiation = sum(row['avg_radiation'] * row['orientation_count'] for row in rows if row['avg_radiation']) / total_elements
                
                orientation_breakdown = {row['orientation']: row['orientation_count'] for row in rows}
                energy_breakdown = {
                    row['orientation']: row['avg_radiation'] * row['total_area'] 
                    for row in rows if row['avg_radiation'] and row['total_area']
                }
                
                return ProjectRadiationSummary(
                    project_id=project_id,
                    total_elements=total_elements,
                    suitable_elements=total_elements,  # All queried elements are suitable
                    total_glass_area=total_area or 0.0,
                    avg_annual_radiation=avg_radiation or 0.0,
                    orientation_breakdown=orientation_breakdown,
                    energy_breakdown=energy_breakdown,
                    processing_stats={"method": "database_aggregation"},
                    analysis_settings={"precision": "variable"}
                )
                
        except Exception as e:
            logger.error(f"Failed to get radiation summary: {e}")
            return None
    
    def get_radiation_summary_sync(self, project_id: int) -> Optional[ProjectRadiationSummary]:
        """Get radiation analysis summary synchronously."""
        try:
            with self.connection_manager.get_sync_connection() as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                    cursor.execute(SQL_QUERIES["get_radiation_summary"], (project_id,))
                    rows = cursor.fetchall()
                    
                    if not rows:
                        return None
                    
                    # Aggregate results
                    total_elements = sum(row['orientation_count'] for row in rows)
                    total_area = sum(row['total_area'] for row in rows if row['total_area'])
                    avg_radiation = sum(row['avg_radiation'] * row['orientation_count'] for row in rows if row['avg_radiation']) / total_elements
                    
                    orientation_breakdown = {row['orientation']: row['orientation_count'] for row in rows}
                    energy_breakdown = {
                        row['orientation']: row['avg_radiation'] * row['total_area'] 
                        for row in rows if row['avg_radiation'] and row['total_area']
                    }
                    
                    return ProjectRadiationSummary(
                        project_id=project_id,
                        total_elements=total_elements,
                        suitable_elements=total_elements,
                        total_glass_area=total_area or 0.0,
                        avg_annual_radiation=avg_radiation or 0.0,
                        orientation_breakdown=orientation_breakdown,
                        energy_breakdown=energy_breakdown,
                        processing_stats={"method": "database_aggregation"},
                        analysis_settings={"precision": "variable"}
                    )
                    
        except Exception as e:
            logger.error(f"Failed to get radiation summary: {e}")
            return None
    
    async def clear_radiation_data_async(self, project_id: int) -> DatabaseMetrics:
        """Clear existing radiation data asynchronously."""
        start_time = datetime.now()
        
        try:
            async with self.connection_manager.get_async_connection() as conn:
                query = SQL_QUERIES["clear_radiation_data"]
                result = await conn.execute(query, project_id)
                
                # Extract row count from result
                rows_affected = int(result.split()[-1]) if "DELETE" in result else 0
                
                execution_time = (datetime.now() - start_time).total_seconds()
                
                return DatabaseMetrics(
                    operation="clear_radiation_data",
                    table_name="element_radiation",
                    rows_affected=rows_affected,
                    execution_time=execution_time,
                    success=True
                )
                
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"Clear radiation data failed: {e}")
            return DatabaseMetrics(
                operation="clear_radiation_data",
                table_name="element_radiation",
                rows_affected=0,
                execution_time=execution_time,
                success=False,
                error_message=str(e)
            )
    
    def clear_radiation_data_sync(self, project_id: int) -> DatabaseMetrics:
        """Clear existing radiation data synchronously."""
        start_time = datetime.now()
        
        try:
            with self.connection_manager.get_sync_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(SQL_QUERIES["clear_radiation_data"], (project_id,))
                    rows_affected = cursor.rowcount
                    conn.commit()
                    
                    execution_time = (datetime.now() - start_time).total_seconds()
                    
                    return DatabaseMetrics(
                        operation="clear_radiation_data",
                        table_name="element_radiation",
                        rows_affected=rows_affected,
                        execution_time=execution_time,
                        success=True
                    )
                    
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"Clear radiation data failed: {e}")
            return DatabaseMetrics(
                operation="clear_radiation_data",
                table_name="element_radiation",
                rows_affected=0,
                execution_time=execution_time,
                success=False,
                error_message=str(e)
            )


class AggregationQueries:
    """SQL views and functions for heavy aggregations."""
    
    def __init__(self):
        self.connection_manager = DatabaseConnectionManager()
    
    def create_aggregation_views(self):
        """Create SQL views for common aggregations."""
        views = [
            """
            CREATE OR REPLACE VIEW radiation_orientation_stats AS
            SELECT 
                project_id,
                orientation,
                COUNT(*) as element_count,
                AVG(annual_radiation) as avg_radiation,
                SUM(annual_radiation * glass_area) as total_energy_potential,
                MIN(annual_radiation) as min_radiation,
                MAX(annual_radiation) as max_radiation,
                STDDEV(annual_radiation) as radiation_stddev
            FROM element_radiation
            GROUP BY project_id, orientation;
            """,
            
            """
            CREATE OR REPLACE VIEW project_radiation_overview AS
            SELECT 
                er.project_id,
                COUNT(er.element_id) as total_analyzed_elements,
                COUNT(be.element_id) as total_suitable_elements,
                AVG(er.annual_radiation) as avg_annual_radiation,
                SUM(er.glass_area) as total_glass_area,
                SUM(er.annual_radiation * er.glass_area) as total_annual_energy,
                MIN(er.calculated_at) as analysis_start,
                MAX(er.calculated_at) as analysis_completion
            FROM element_radiation er
            LEFT JOIN building_elements be ON er.project_id = be.project_id AND er.element_id = be.element_id
            GROUP BY er.project_id;
            """,
            
            """
            CREATE OR REPLACE VIEW radiation_performance_ranking AS
            SELECT 
                project_id,
                element_id,
                orientation,
                annual_radiation,
                glass_area,
                (annual_radiation * glass_area) as energy_potential,
                RANK() OVER (PARTITION BY project_id ORDER BY annual_radiation DESC) as radiation_rank,
                RANK() OVER (PARTITION BY project_id ORDER BY (annual_radiation * glass_area) DESC) as energy_rank
            FROM element_radiation;
            """
        ]
        
        try:
            with self.connection_manager.get_sync_connection() as conn:
                with conn.cursor() as cursor:
                    for view_sql in views:
                        cursor.execute(view_sql)
                    conn.commit()
                    logger.info("Created aggregation views successfully")
        except Exception as e:
            logger.error(f"Failed to create aggregation views: {e}")
    
    async def get_orientation_stats_async(self, project_id: int) -> List[Dict[str, Any]]:
        """Get orientation statistics using SQL view."""
        async with self.connection_manager.get_async_connection() as conn:
            query = """
                SELECT * FROM radiation_orientation_stats 
                WHERE project_id = $1 
                ORDER BY avg_radiation DESC
            """
            rows = await conn.fetch(query, project_id)
            return [dict(row) for row in rows]
    
    async def get_top_performing_elements_async(self, project_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """Get top performing elements by energy potential."""
        async with self.connection_manager.get_async_connection() as conn:
            query = """
                SELECT * FROM radiation_performance_ranking 
                WHERE project_id = $1 
                ORDER BY energy_potential DESC 
                LIMIT $2
            """
            rows = await conn.fetch(query, project_id, limit)
            return [dict(row) for row in rows]


class IndexManager:
    """Database index management for optimization."""
    
    def __init__(self):
        self.connection_manager = DatabaseConnectionManager()
    
    def ensure_indexes(self):
        """Ensure all required indexes exist."""
        from ..config import INDEX_STATEMENTS
        
        try:
            with self.connection_manager.get_sync_connection() as conn:
                with conn.cursor() as cursor:
                    for index_sql in INDEX_STATEMENTS:
                        cursor.execute(index_sql)
                        logger.debug(f"Ensured index: {index_sql}")
                    conn.commit()
                    logger.info("All database indexes ensured")
        except Exception as e:
            logger.error(f"Failed to ensure indexes: {e}")
    
    def analyze_query_performance(self, query: str, params: tuple = None) -> Dict[str, Any]:
        """Analyze query performance using EXPLAIN ANALYZE."""
        try:
            with self.connection_manager.get_sync_connection() as conn:
                with conn.cursor() as cursor:
                    explain_query = f"EXPLAIN ANALYZE {query}"
                    cursor.execute(explain_query, params)
                    results = cursor.fetchall()
                    
                    return {
                        "query": query,
                        "params": params,
                        "plan": [row[0] for row in results],
                        "analyzed_at": datetime.now()
                    }
        except Exception as e:
            logger.error(f"Query analysis failed: {e}")
            return {"error": str(e)}


# Global instances
radiation_queries = RadiationDataQueries()
aggregation_queries = AggregationQueries()
index_manager = IndexManager()


async def execute_with_fallback(async_func, sync_func, *args, **kwargs):
    """Execute async function with sync fallback."""
    try:
        # Try async first
        return await async_func(*args, **kwargs)
    except Exception as e:
        logger.warning(f"Async execution failed, falling back to sync: {e}")
        # Fallback to sync
        return sync_func(*args, **kwargs)