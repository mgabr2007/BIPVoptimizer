"""
Unified Analysis Logger
Single source of truth for all radiation analysis logging to prevent duplicates
"""

import streamlit as st
import time
from datetime import datetime
from typing import Set, Dict, Optional

class UnifiedAnalysisLogger:
    def __init__(self):
        self.start_time = time.time()
        self.logged_events: Set[str] = set()  # Track unique events
        self.log_messages = []
        self.element_status: Dict[str, str] = {}  # Track element status
        self.container: Optional[st.container] = None
        
        # Metrics
        self.total_processed = 0
        self.successful = 0
        self.failed = 0
        self.skipped = 0
    
    def create_display(self):
        """Create the unified log display"""
        st.subheader("📋 Live Processing Log")
        
        # Create metrics display
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            self.processed_metric = st.empty()
        with col2:
            self.success_metric = st.empty()
        with col3:
            self.error_metric = st.empty()
        with col4:
            self.skip_metric = st.empty()
        
        # Create log container
        self.container = st.container()
        self.update_metrics()
        return self
    
    def _generate_event_key(self, element_id: str, event_type: str, timestamp: str) -> str:
        """Generate unique key for event deduplication"""
        return f"{element_id}_{event_type}_{timestamp}"
    
    def _add_log_message(self, message: str, element_id: str, event_type: str):
        """Add message with strict deduplication"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        event_key = self._generate_event_key(element_id, event_type, timestamp)
        
        # Prevent duplicate events
        if event_key in self.logged_events:
            return False
        
        # Add to logged events
        self.logged_events.add(event_key)
        
        # Add timestamped message
        timestamped_message = f"[{timestamp}] {message}"
        self.log_messages.append(timestamped_message)
        
        # Keep only last 10 messages
        if len(self.log_messages) > 10:
            self.log_messages.pop(0)
        
        # Update display
        self._update_display()
        return True
    
    def _update_display(self):
        """Update the log display"""
        if self.container:
            with self.container:
                # Clear and show latest messages
                for msg in self.log_messages[-5:]:  # Show last 5 messages
                    st.text(msg)
        self.update_metrics()
    
    def update_metrics(self):
        """Update metrics display"""
        if hasattr(self, 'processed_metric'):
            self.processed_metric.metric("Elements Processed", self.total_processed)
            self.success_metric.metric("Successful", self.successful, 
                                     delta=f"{(self.successful/max(1,self.total_processed)*100):.1f}%")
            self.error_metric.metric("Errors", self.failed)
            self.skip_metric.metric("Skipped", self.skipped)
    
    def log_element_start(self, element_id: str, orientation: str, area: float) -> bool:
        """Log element processing start - guaranteed single entry"""
        # Check if already processing this element
        if self.element_status.get(element_id) == "processing":
            return False  # Already logged
        
        # Update status
        self.element_status[element_id] = "processing"
        self.total_processed += 1
        
        # Add log message
        message = f"🔄 Processing {element_id} ({orientation}, {area:.1f}m²)"
        return self._add_log_message(message, element_id, "start")
    
    def log_element_success(self, element_id: str, annual_radiation: float, processing_time: float) -> bool:
        """Log element success - guaranteed single entry"""
        # Check if already completed
        if self.element_status.get(element_id) == "completed":
            return False  # Already logged
        
        # Update status
        self.element_status[element_id] = "completed"
        self.successful += 1
        
        # Add log message
        message = f"✅ {element_id} completed ({annual_radiation:.0f} kWh/m²/year, {processing_time:.2f}s)"
        return self._add_log_message(message, element_id, "success")
    
    def log_element_error(self, element_id: str, error_message: str, processing_time: float) -> bool:
        """Log element error - guaranteed single entry"""
        # Check if already failed
        if self.element_status.get(element_id) == "failed":
            return False  # Already logged
        
        # Update status
        self.element_status[element_id] = "failed"
        self.failed += 1
        
        # Add log message
        short_error = error_message[:50] + "..." if len(error_message) > 50 else error_message
        message = f"❌ {element_id} failed ({short_error}, {processing_time:.2f}s)"
        return self._add_log_message(message, element_id, "error")
    
    def log_element_skip(self, element_id: str, reason: str) -> bool:
        """Log element skip - guaranteed single entry"""
        # Check if already skipped
        if self.element_status.get(element_id) == "skipped":
            return False  # Already logged
        
        # Update status
        self.element_status[element_id] = "skipped"
        self.skipped += 1
        
        # Add log message
        message = f"⏭️ {element_id} skipped ({reason})"
        return self._add_log_message(message, element_id, "skip")
    
    def get_summary(self) -> dict:
        """Get analysis summary"""
        elapsed_time = time.time() - self.start_time
        return {
            'total_time': elapsed_time,
            'elements_processed': self.total_processed,
            'success_rate': (self.successful / max(1, self.total_processed)) * 100,
            'error_rate': (self.failed / max(1, self.total_processed)) * 100,
            'unique_events': len(self.logged_events)
        }
    
    def reset(self):
        """Reset logger state"""
        self.logged_events.clear()
        self.log_messages.clear()
        self.element_status.clear()
        self.total_processed = 0
        self.successful = 0
        self.failed = 0
        self.skipped = 0
        self.start_time = time.time()

# Global unified logger instance
unified_logger = UnifiedAnalysisLogger()