"""
Real-time Analysis Monitor
Shows live debugging information during radiation analysis
"""

import streamlit as st
import time
from datetime import datetime

class AnalysisMonitor:
    def __init__(self):
        self.start_time = time.time()
        self.element_count = 0
        self.success_count = 0
        self.error_count = 0
        self.skip_count = 0
        
    def create_monitor_display(self):
        """Create the monitoring dashboard"""
        st.subheader("🔍 Live Analysis Monitor")
        
        # Create columns for metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            self.processed_metric = st.empty()
        with col2:
            self.success_metric = st.empty()
        with col3:
            self.error_metric = st.empty()
        with col4:
            self.skip_metric = st.empty()
        
        # Create live log display
        st.write("**Live Processing Log:**")
        self.log_container = st.container()
        self.log_messages = []
        
        # Current element display
        self.current_element = st.empty()
        
        return self
    
    def update_metrics(self):
        """Update the live metrics"""
        self.processed_metric.metric("Elements Processed", self.element_count)
        self.success_metric.metric("Successful", self.success_count, delta=f"{(self.success_count/max(1,self.element_count)*100):.1f}%")
        self.error_metric.metric("Errors", self.error_count)
        self.skip_metric.metric("Skipped", self.skip_count)
    
    def log_element_start(self, element_id, orientation, area):
        """Log element processing start"""
        self.element_count += 1
        timestamp = datetime.now().strftime("%H:%M:%S")
        message = f"[{timestamp}] 🔄 Processing {element_id} ({orientation}, {area:.1f}m²)"
        self.log_messages.append(message)
        
        # Keep only last 10 messages
        if len(self.log_messages) > 10:
            self.log_messages.pop(0)
        
        # Update displays
        self.current_element.write(f"**Current:** {element_id}")
        with self.log_container:
            for msg in self.log_messages[-5:]:  # Show last 5 messages
                st.text(msg)
        self.update_metrics()
    
    def log_element_success(self, element_id, annual_radiation, processing_time):
        """Log successful element processing"""
        self.success_count += 1
        timestamp = datetime.now().strftime("%H:%M:%S")
        message = f"[{timestamp}] ✅ {element_id} completed ({annual_radiation:.0f} kWh/m²/year, {processing_time:.2f}s)"
        self.log_messages.append(message)
        
        if len(self.log_messages) > 10:
            self.log_messages.pop(0)
        
        with self.log_container:
            for msg in self.log_messages[-5:]:
                st.text(msg)
        self.update_metrics()
    
    def log_element_error(self, element_id, error_message, processing_time):
        """Log failed element processing"""
        self.error_count += 1
        timestamp = datetime.now().strftime("%H:%M:%S")
        message = f"[{timestamp}] ❌ {element_id} failed ({error_message[:50]}..., {processing_time:.2f}s)"
        self.log_messages.append(message)
        
        if len(self.log_messages) > 10:
            self.log_messages.pop(0)
        
        with self.log_container:
            for msg in self.log_messages[-5:]:
                st.text(msg)
        self.update_metrics()
    
    def log_element_skip(self, element_id, reason):
        """Log skipped element"""
        self.skip_count += 1
        timestamp = datetime.now().strftime("%H:%M:%S")
        message = f"[{timestamp}] ⏭️ {element_id} skipped ({reason})"
        self.log_messages.append(message)
        
        if len(self.log_messages) > 10:
            self.log_messages.pop(0)
        
        with self.log_container:
            for msg in self.log_messages[-5:]:
                st.text(msg)
        self.update_metrics()
    
    def log_timeout(self, remaining_elements):
        """Log timeout event"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        message = f"[{timestamp}] ⏱️ Session timeout - {remaining_elements} elements remaining"
        self.log_messages.append(message)
        
        with self.log_container:
            for msg in self.log_messages[-5:]:
                st.text(msg)
    
    def get_summary(self):
        """Get analysis summary"""
        elapsed_time = time.time() - self.start_time
        return {
            'total_time': elapsed_time,
            'elements_processed': self.element_count,
            'success_rate': (self.success_count / max(1, self.element_count)) * 100,
            'error_rate': (self.error_count / max(1, self.element_count)) * 100
        }

# Global monitor instance
analysis_monitor = AnalysisMonitor()