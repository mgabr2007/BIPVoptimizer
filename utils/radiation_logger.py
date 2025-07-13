"""
Radiation Analysis Logger
Dedicated logging system for radiation analysis outcomes
"""

import streamlit as st
import psycopg2
from datetime import datetime
import time

class RadiationLogger:
    def __init__(self):
        self.session_start_time = time.time()
        self.session_batch = int(time.time())
        self.EMIT_CONSOLE = False  # Silenced to prevent duplicate logging
        
    def get_connection(self):
        """Get database connection"""
        try:
            import os
            database_url = os.environ.get('DATABASE_URL')
            if database_url:
                conn = psycopg2.connect(database_url)
                return conn
        except Exception as e:
            if self.EMIT_CONSOLE:
                st.error(f"Database connection failed: {e}")
        return None
    
    def log_element_start(self, project_id, element_id, orientation, area):
        """Log when element processing starts"""
        try:
            conn = self.get_connection()
            if conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        INSERT INTO radiation_analysis_log 
                        (project_id, element_id, analysis_timestamp, status, orientation, area_m2, session_batch)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """, (project_id, element_id, datetime.now(), 'processing', orientation, area, self.session_batch))
                    conn.commit()
                conn.close()
        except Exception as e:
            if self.EMIT_CONSOLE:
                st.warning(f"Could not log element start: {e}")
    
    def log_element_success(self, project_id, element_id, annual_radiation, peak_irradiance, processing_time):
        """Log successful element processing"""
        try:
            conn = self.get_connection()
            if conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        UPDATE radiation_analysis_log 
                        SET status = %s, annual_radiation = %s, peak_irradiance = %s, 
                            processing_time_seconds = %s
                        WHERE project_id = %s AND element_id = %s AND session_batch = %s
                    """, ('completed', annual_radiation, peak_irradiance, processing_time, 
                         project_id, element_id, self.session_batch))
                    conn.commit()
                conn.close()
        except Exception as e:
            if self.EMIT_CONSOLE:
                st.warning(f"Could not log element success: {e}")
    
    def log_element_failure(self, project_id, element_id, error_message, processing_time):
        """Log failed element processing"""
        try:
            conn = self.get_connection()
            if conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        UPDATE radiation_analysis_log 
                        SET status = %s, error_message = %s, processing_time_seconds = %s
                        WHERE project_id = %s AND element_id = %s AND session_batch = %s
                    """, ('failed', str(error_message)[:500], processing_time, 
                         project_id, element_id, self.session_batch))
                    conn.commit()
                conn.close()
        except Exception as e:
            if self.EMIT_CONSOLE:
                st.warning(f"Could not log element failure: {e}")
    
    def log_element_skip(self, project_id, element_id, reason):
        """Log skipped element processing"""
        try:
            conn = self.get_connection()
            if conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        INSERT INTO radiation_analysis_log 
                        (project_id, element_id, analysis_timestamp, status, error_message, session_batch)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """, (project_id, element_id, datetime.now(), 'skipped', reason, self.session_batch))
                    conn.commit()
                conn.close()
        except Exception as e:
            if self.EMIT_CONSOLE:
                st.warning(f"Could not log element skip: {e}")
    
    def log_analysis_summary(self, project_id, total_elements, processed_elements, failed_elements, skipped_elements, completion_status, notes=""):
        """Log overall analysis summary"""
        try:
            analysis_duration = (time.time() - self.session_start_time) / 60  # Convert to minutes
            conn = self.get_connection()
            if conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        INSERT INTO radiation_analysis_summary 
                        (project_id, total_elements, processed_elements, failed_elements, 
                         skipped_elements, analysis_duration_minutes, completion_status, notes)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """, (project_id, total_elements, processed_elements, failed_elements, 
                         skipped_elements, analysis_duration, completion_status, notes))
                    conn.commit()
                conn.close()
        except Exception as e:
            if self.EMIT_CONSOLE:
                st.warning(f"Could not log analysis summary: {e}")
    
    def get_analysis_status(self, project_id):
        """Get current analysis status from database"""
        try:
            conn = self.get_connection()
            if conn:
                with conn.cursor() as cursor:
                    # Get latest analysis summary
                    cursor.execute("""
                        SELECT total_elements, processed_elements, failed_elements, 
                               skipped_elements, completion_status, analysis_date
                        FROM radiation_analysis_summary 
                        WHERE project_id = %s 
                        ORDER BY analysis_date DESC LIMIT 1
                    """, (project_id,))
                    summary = cursor.fetchone()
                    
                    # Get detailed element status
                    cursor.execute("""
                        SELECT status, COUNT(*) as count
                        FROM radiation_analysis_log 
                        WHERE project_id = %s 
                        GROUP BY status
                    """, (project_id,))
                    status_counts = dict(cursor.fetchall())
                    
                conn.close()
                return {
                    'summary': summary,
                    'status_counts': status_counts
                }
        except Exception as e:
            if self.EMIT_CONSOLE:
                st.warning(f"Could not get analysis status: {e}")
        return None
    
    def display_analysis_status(self, project_id):
        """Display current analysis status (silenced to prevent duplicate UI)"""
        if self.EMIT_CONSOLE:
            status = self.get_analysis_status(project_id)
            if status:
                st.subheader("📊 Analysis Status Dashboard")
                
                if status['summary']:
                    total, processed, failed, skipped, completion, date = status['summary']
                    
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Total Elements", total)
                    with col2:
                        st.metric("Processed", processed, delta=f"{(processed/total*100):.1f}%")
                    with col3:
                        st.metric("Failed", failed, delta=f"{(failed/total*100):.1f}%")
                    with col4:
                        st.metric("Skipped", skipped, delta=f"{(skipped/total*100):.1f}%")
                    
                    st.info(f"Last analysis: {date} - Status: {completion}")
                
                if status['status_counts']:
                    st.write("**Current Element Status:**")
                    for status_type, count in status['status_counts'].items():
                        st.write(f"- {status_type.title()}: {count} elements")

# Global logger instance
radiation_logger = RadiationLogger()