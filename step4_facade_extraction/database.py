"""
Enhanced database operations for facade extraction with async/bulk capabilities.
"""

import asyncio
import asyncpg
import psycopg2
import psycopg2.extras
from psycopg2.extras import execute_values, RealDictCursor
from contextlib import asynccontextmanager, contextmanager
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
from concurrent.futures import ThreadPoolExecutor
import os
from .models import WindowRecord, WallRecord, ProcessingResult
from .config import get_config
from .logging_utils import get_logger, log_operation


class DatabaseConnectionManager:
    """Enhanced database connection manager with context managers."""
    
    def __init__(self, project_id: Optional[int] = None):
        self.config = get_config()
        self.logger = get_logger(project_id)
        self._connection_pool = None
    
    def _get_connection_params(self) -> Dict[str, str]:
        """Get connection parameters from environment or Streamlit secrets."""
        # Try environment variables first
        params = {
            'host': os.getenv('PGHOST', 'localhost'),
            'port': os.getenv('PGPORT', '5432'),
            'database': os.getenv('PGDATABASE', 'postgres'),
            'user': os.getenv('PGUSER', 'postgres'),
            'password': os.getenv('PGPASSWORD', '')
        }
        
        # Try Streamlit secrets if available
        try:
            import streamlit as st
            if hasattr(st, 'secrets') and 'database' in st.secrets:
                secrets = st.secrets['database']
                params.update({
                    'host': secrets.get('host', params['host']),
                    'port': str(secrets.get('port', params['port'])),
                    'database': secrets.get('database', params['database']),
                    'user': secrets.get('user', params['user']),
                    'password': secrets.get('password', params['password'])
                })
        except ImportError:
            pass  # Streamlit not available
        
        return params
    
    @contextmanager
    def get_connection(self):
        """Get a synchronous database connection with context management."""
        params = self._get_connection_params()
        conn = None
        
        try:
            conn = psycopg2.connect(**params)
            conn.autocommit = False
            self.logger.debug("Database connection established")
            yield conn
            
        except Exception as e:
            if conn:
                conn.rollback()
            self.logger.error(f"Database connection error: {str(e)}")
            raise
        finally:
            if conn:
                conn.close()
                self.logger.debug("Database connection closed")
    
    @asynccontextmanager
    async def get_async_connection(self):
        """Get an async database connection."""
        params = self._get_connection_params()
        conn = None
        
        try:
            conn = await asyncpg.connect(
                host=params['host'],
                port=int(params['port']),
                database=params['database'],
                user=params['user'],
                password=params['password']
            )
            self.logger.debug("Async database connection established")
            yield conn
            
        except Exception as e:
            self.logger.error(f"Async database connection error: {str(e)}")
            raise
        finally:
            if conn:
                await conn.close()
                self.logger.debug("Async database connection closed")


class BulkDatabaseOperations:
    """High-performance bulk database operations."""
    
    def __init__(self, project_id: Optional[int] = None):
        self.config = get_config()
        self.logger = get_logger(project_id)
        self.connection_manager = DatabaseConnectionManager(project_id)
        self.executor = ThreadPoolExecutor(max_workers=4)
    
    def bulk_upsert_windows(self, windows: List[WindowRecord]) -> ProcessingResult:
        """Bulk upsert window records using UPSERT pattern."""
        with log_operation(self.logger, "bulk_upsert_windows", count=len(windows)):
            try:
                with self.connection_manager.get_connection() as conn:
                    with conn.cursor() as cursor:
                        # Prepare data for bulk insert
                        values = [
                            (
                                w.project_id, w.element_id, w.family, w.element_type,
                                w.glass_area, w.window_width, w.window_height,
                                w.building_level, w.wall_element_id, w.azimuth,
                                w.orientation.value, w.pv_suitable, w.created_at
                            )
                            for w in windows
                        ]
                        
                        # UPSERT query
                        upsert_query = """
                        INSERT INTO building_elements 
                        (project_id, element_id, family, element_type, glass_area, 
                         window_width, window_height, building_level, wall_element_id, 
                         azimuth, orientation, pv_suitable, created_at)
                        VALUES %s
                        ON CONFLICT (project_id, element_id) 
                        DO UPDATE SET
                            family = EXCLUDED.family,
                            element_type = EXCLUDED.element_type,
                            glass_area = EXCLUDED.glass_area,
                            window_width = EXCLUDED.window_width,
                            window_height = EXCLUDED.window_height,
                            building_level = EXCLUDED.building_level,
                            wall_element_id = EXCLUDED.wall_element_id,
                            azimuth = EXCLUDED.azimuth,
                            orientation = EXCLUDED.orientation,
                            pv_suitable = EXCLUDED.pv_suitable,
                            created_at = EXCLUDED.created_at
                        """
                        
                        # Execute bulk upsert
                        execute_values(
                            cursor, upsert_query, values,
                            template=None, page_size=self.config.database.batch_size
                        )
                        
                        conn.commit()
                        
                        self.logger.log_database_operation(
                            "UPSERT", "building_elements", len(windows)
                        )
                        
                        return ProcessingResult(
                            success=True,
                            total_elements=len(windows),
                            processed_elements=len(windows)
                        )
                        
            except Exception as e:
                self.logger.error(f"Bulk upsert windows failed: {str(e)}")
                return ProcessingResult(
                    success=False,
                    errors=[str(e)]
                )
    
    def bulk_upsert_walls(self, walls: List[WallRecord]) -> ProcessingResult:
        """Bulk upsert wall records."""
        with log_operation(self.logger, "bulk_upsert_walls", count=len(walls)):
            try:
                with self.connection_manager.get_connection() as conn:
                    with conn.cursor() as cursor:
                        # Prepare data for bulk insert
                        values = [
                            (
                                w.project_id, w.element_id, w.element_id,  # name = element_id for now
                                w.wall_type, w.building_level, w.area, w.azimuth,
                                w.orientation.value, w.created_at
                            )
                            for w in walls
                        ]
                        
                        # UPSERT query
                        upsert_query = """
                        INSERT INTO building_walls 
                        (project_id, element_id, name, wall_type, level, area, 
                         azimuth, orientation, created_at)
                        VALUES %s
                        ON CONFLICT (project_id, element_id) 
                        DO UPDATE SET
                            name = EXCLUDED.name,
                            wall_type = EXCLUDED.wall_type,
                            level = EXCLUDED.level,
                            area = EXCLUDED.area,
                            azimuth = EXCLUDED.azimuth,
                            orientation = EXCLUDED.orientation,
                            created_at = EXCLUDED.created_at
                        """
                        
                        # Execute bulk upsert
                        execute_values(
                            cursor, upsert_query, values,
                            template=None, page_size=self.config.database.batch_size
                        )
                        
                        conn.commit()
                        
                        self.logger.log_database_operation(
                            "UPSERT", "building_walls", len(walls)
                        )
                        
                        return ProcessingResult(
                            success=True,
                            total_elements=len(walls),
                            processed_elements=len(walls)
                        )
                        
            except Exception as e:
                self.logger.error(f"Bulk upsert walls failed: {str(e)}")
                return ProcessingResult(
                    success=False,
                    errors=[str(e)]
                )
    
    async def async_bulk_upsert_windows(self, windows: List[WindowRecord]) -> ProcessingResult:
        """Async bulk upsert for better UI responsiveness."""
        try:
            async with self.connection_manager.get_async_connection() as conn:
                # Prepare values
                values = [
                    (
                        w.project_id, w.element_id, w.family, w.element_type,
                        w.glass_area, w.window_width, w.window_height,
                        w.building_level, w.wall_element_id, w.azimuth,
                        w.orientation.value, w.pv_suitable, w.created_at
                    )
                    for w in windows
                ]
                
                # Execute async bulk insert
                await conn.executemany("""
                    INSERT INTO building_elements 
                    (project_id, element_id, family, element_type, glass_area, 
                     window_width, window_height, building_level, wall_element_id, 
                     azimuth, orientation, pv_suitable, created_at)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
                    ON CONFLICT (project_id, element_id) 
                    DO UPDATE SET
                        family = EXCLUDED.family,
                        glass_area = EXCLUDED.glass_area,
                        azimuth = EXCLUDED.azimuth,
                        orientation = EXCLUDED.orientation,
                        pv_suitable = EXCLUDED.pv_suitable
                """, values)
                
                return ProcessingResult(
                    success=True,
                    total_elements=len(windows),
                    processed_elements=len(windows)
                )
                
        except Exception as e:
            self.logger.error(f"Async bulk upsert failed: {str(e)}")
            return ProcessingResult(
                success=False,
                errors=[str(e)]
            )
    
    def check_duplicates_in_db(self, project_id: int, element_ids: List[str], table: str) -> List[str]:
        """Check for existing element IDs in database."""
        try:
            with self.connection_manager.get_connection() as conn:
                with conn.cursor() as cursor:
                    # Create temporary table for element IDs
                    cursor.execute("CREATE TEMP TABLE temp_element_ids (element_id TEXT)")
                    
                    # Insert element IDs to check
                    execute_values(
                        cursor,
                        "INSERT INTO temp_element_ids VALUES %s",
                        [(eid,) for eid in element_ids]
                    )
                    
                    # Find duplicates
                    cursor.execute(f"""
                        SELECT t.element_id 
                        FROM temp_element_ids t
                        INNER JOIN {table} b ON t.element_id = b.element_id 
                        WHERE b.project_id = %s
                    """, (project_id,))
                    
                    duplicates = [row[0] for row in cursor.fetchall()]
                    return duplicates
                    
        except Exception as e:
            self.logger.error(f"Error checking duplicates: {str(e)}")
            return []
    
    def ensure_database_indices(self):
        """Ensure required database indices exist."""
        indices = [
            ("idx_building_elements_project_id", "building_elements", "project_id"),
            ("idx_building_elements_element_id", "building_elements", "element_id"),
            ("idx_building_elements_wall_element_id", "building_elements", "wall_element_id"),
            ("idx_building_walls_project_id", "building_walls", "project_id"),
            ("idx_building_walls_element_id", "building_walls", "element_id"),
        ]
        
        try:
            with self.connection_manager.get_connection() as conn:
                with conn.cursor() as cursor:
                    for index_name, table, column in indices:
                        try:
                            cursor.execute(f"""
                                CREATE INDEX IF NOT EXISTS {index_name} 
                                ON {table} ({column})
                            """)
                            self.logger.debug(f"Ensured index {index_name}")
                        except Exception as e:
                            self.logger.warning(f"Could not create index {index_name}: {str(e)}")
                    
                    conn.commit()
                    
        except Exception as e:
            self.logger.error(f"Error ensuring indices: {str(e)}")


class DataAccessLayer:
    """Data access layer for facade extraction operations."""
    
    def __init__(self, project_id: Optional[int] = None):
        self.connection_manager = DatabaseConnectionManager(project_id)
        self.logger = get_logger(project_id)
    
    def get_project_elements_count(self, project_id: int) -> Tuple[int, int]:
        """Get count of windows and walls for a project."""
        try:
            with self.connection_manager.get_connection() as conn:
                with conn.cursor() as cursor:
                    # Count windows
                    cursor.execute("""
                        SELECT COUNT(*) FROM building_elements WHERE project_id = %s
                    """, (project_id,))
                    window_count = cursor.fetchone()[0]
                    
                    # Count walls
                    cursor.execute("""
                        SELECT COUNT(*) FROM building_walls WHERE project_id = %s
                    """, (project_id,))
                    wall_count = cursor.fetchone()[0]
                    
                    return window_count, wall_count
                    
        except Exception as e:
            self.logger.error(f"Error getting element counts: {str(e)}")
            return 0, 0
    
    def get_existing_uploads(self, project_id: int) -> Dict[str, Any]:
        """Get information about existing uploads for a project."""
        try:
            with self.connection_manager.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    # Get window upload info
                    cursor.execute("""
                        SELECT COUNT(*) as count, MAX(created_at) as last_upload
                        FROM building_elements WHERE project_id = %s
                    """, (project_id,))
                    window_info = cursor.fetchone()
                    
                    # Get wall upload info
                    cursor.execute("""
                        SELECT COUNT(*) as count, MAX(created_at) as last_upload
                        FROM building_walls WHERE project_id = %s
                    """, (project_id,))
                    wall_info = cursor.fetchone()
                    
                    return {
                        'windows': dict(window_info) if window_info else {'count': 0, 'last_upload': None},
                        'walls': dict(wall_info) if wall_info else {'count': 0, 'last_upload': None}
                    }
                    
        except Exception as e:
            self.logger.error(f"Error getting upload info: {str(e)}")
            return {'windows': {'count': 0, 'last_upload': None}, 'walls': {'count': 0, 'last_upload': None}}
    
    def clear_project_data(self, project_id: int, data_type: str = "all") -> bool:
        """Clear existing project data."""
        try:
            with self.connection_manager.get_connection() as conn:
                with conn.cursor() as cursor:
                    if data_type in ["windows", "all"]:
                        cursor.execute("DELETE FROM building_elements WHERE project_id = %s", (project_id,))
                        
                    if data_type in ["walls", "all"]:
                        cursor.execute("DELETE FROM building_walls WHERE project_id = %s", (project_id,))
                    
                    conn.commit()
                    self.logger.log_database_operation("DELETE", f"project_{project_id}_{data_type}", cursor.rowcount)
                    return True
                    
        except Exception as e:
            self.logger.error(f"Error clearing project data: {str(e)}")
            return False