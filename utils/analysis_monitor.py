"""
Real-time Analysis Monitor
Shows live debugging information during radiation analysis
"""

import streamlit as st
import time
from datetime import datetime
from .element_registry import get_global_registry

class AnalysisMonitor:
    def __init__(self):
        self.start_time = time.time()
        self.element_count = 0
        self.success_count = 0
        self.error_count = 0
        self.skip_count = 0
        # Add deduplication tracking for log messages
        self._last_logged = {"id": None, "status": None, "timestamp": 0}
        
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
    
    def _should_log_message(self, element_id, status):
        """Check if message should be logged (prevents duplicate console output)"""
        now = time.time()
        last = self._last_logged
        
        # Skip if same element and status within 1 second (prevents duplicate logger output)
        if (element_id, status) == (last["id"], last["status"]) and now - last["timestamp"] < 1:
            return False
        
        # Update tracking
        self._last_logged = {"id": element_id, "status": status, "timestamp": now}
        return True

    def log_element_start(self, element_id, orientation, area):
        """Log element processing start with comprehensive duplication prevention"""
        # Check for duplicate message (prevents multiple logger output)
        if not self._should_log_message(element_id, "processing"):
            return False
            
        # Use global registry for comprehensive deduplication
        registry = get_global_registry()
        
        # Try to register element for processing
        success, message = registry.start_processing(element_id)
        if not success:
            # Element already being processed - skip logging
            return False
        
        # Initialize active elements set if needed
        if not hasattr(self, 'active_elements'):
            self.active_elements = set()
        
        # Double-check local active elements
        if element_id in self.active_elements:
            # Clean up registry since we're skipping
            registry.fail_processing(element_id)
            return False
            
        # Add to active elements set
        self.active_elements.add(element_id)
        
        self.element_count += 1
        # Individual element logging removed - only track count
        
        # Keep only last 10 messages
        if len(self.log_messages) > 10:
            self.log_messages.pop(0)
        
        # Update displays
        # Element-by-element display removed as requested
        # Only update metrics, no individual element logging
        self.update_metrics()
        return True
    
    def log_element_success(self, element_id, annual_radiation, processing_time):
        """Log successful element processing"""
        # Check for duplicate message (prevents multiple logger output)
        if not self._should_log_message(element_id, "completed"):
            return False
            
        # Use global registry for comprehensive state management
        registry = get_global_registry()
        
        # Check if element is in processing state
        if registry.get_status(element_id) != "processing":
            # Element not properly registered or already completed - skip logging
            return False
        
        # Mark as completed in global registry
        success, message = registry.complete_processing(element_id)
        if not success:
            # Element not properly registered - skip logging
            return False
        
        # Remove from active elements set
        if hasattr(self, 'active_elements'):
            self.active_elements.discard(element_id)
            
        self.success_count += 1
        # Individual element completion logging removed
        
        if len(self.log_messages) > 10:
            self.log_messages.pop(0)
        
        with self.log_container:
            for msg in self.log_messages[-5:]:
                st.text(msg)
        self.update_metrics()
    
    def log_element_error(self, element_id, error_message, processing_time):
        """Log failed element processing - individual element display removed"""
        # Use global registry for comprehensive state management
        registry = get_global_registry()
        
        # Mark as failed in global registry
        success, message = registry.fail_processing(element_id)
        if not success:
            return False
        
        # Remove from active elements set
        if hasattr(self, 'active_elements'):
            self.active_elements.discard(element_id)
            
        self.error_count += 1
        # Individual element error display removed
        self.update_metrics()
    
    def log_element_skip(self, element_id, reason):
        """Log skipped element - individual element display removed"""
        # Remove from active elements set
        if hasattr(self, 'active_elements'):
            self.active_elements.discard(element_id)
            
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