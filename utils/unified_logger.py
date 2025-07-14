"""
Unified Analysis Logger
Single source of truth for all radiation analysis logging to prevent duplicates
"""

import streamlit as st
import time
import uuid
from datetime import datetime
from typing import Set, Dict, Optional, List

class UnifiedAnalysisLogger:
    def __init__(self):
        self.start_time = time.time()
        self.logged_events: Set[str] = set()  # Track unique events
        self.log_messages: List[Dict] = []  # Store messages with UUIDs
        self.element_status: Dict[str, str] = {}  # Track element status
        self.container: Optional[st.container] = None
        
        # Initialize session state for delta rendering
        if 'displayed_log_ids' not in st.session_state:
            st.session_state.displayed_log_ids = set()
        
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
        
        # Create single log display area for delta rendering
        self.log_display = st.empty()
        self.update_metrics()
        return self
    
    def _generate_event_key(self, element_id: str, event_type: str, timestamp: str) -> str:
        """Generate unique key for event deduplication"""
        return f"{element_id}_{event_type}_{timestamp}"
    
    def _add_log_message(self, message: str, element_id: str, event_type: str):
        """Add message with strict deduplication and delta rendering"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        event_key = self._generate_event_key(element_id, event_type, timestamp)
        
        # Prevent duplicate events
        if event_key in self.logged_events:
            return False
        
        # Add to logged events
        self.logged_events.add(event_key)
        
        # Create message with UUID for delta rendering
        message_entry = {
            'uuid': str(uuid.uuid4()),
            'timestamp': timestamp,
            'message': message,
            'element_id': element_id,
            'event_type': event_type,
            'formatted': f"[{timestamp}] {message}"
        }
        
        self.log_messages.append(message_entry)
        
        # Keep only last 15 messages
        if len(self.log_messages) > 15:
            self.log_messages.pop(0)
        
        # Update display with delta rendering
        self._update_display_delta()
        return True
    
    def _update_display_delta(self):
        """Update the log display using delta rendering to prevent echoes"""
        if not hasattr(self, 'log_display'):
            return
            
        # 🔻 SURGICAL PATCH: Prevent echo messages ——————————————————————————————————————————————
        if "displayed_log_uuids" not in st.session_state:
            st.session_state.displayed_log_uuids = set()
        if "accumulated_log_text" not in st.session_state:
            st.session_state.accumulated_log_text = ""

        new_rows = [row for row in self.log_messages if row["uuid"] not in st.session_state.displayed_log_uuids]
        if new_rows:
            # Add new messages to accumulated text
            for row in new_rows:
                st.session_state.accumulated_log_text += row["formatted"] + "\n"
                st.session_state.displayed_log_uuids.add(row["uuid"])
            
            # Display accumulated text in single container (last 8 lines for readability)
            recent_lines = st.session_state.accumulated_log_text.strip().split('\n')[-8:]
            self.log_display.text('\n'.join(recent_lines))
        # 🔺 END SURGICAL PATCH ——————————————————————————————————————————————————————————————————————
        
        self.update_metrics()
        
    def clear_display(self):
        """Clear the display and reset displayed IDs"""
        if 'displayed_log_uuids' in st.session_state:
            st.session_state.displayed_log_uuids.clear()
        if 'accumulated_log_text' in st.session_state:
            st.session_state.accumulated_log_text = ""
        if hasattr(self, 'log_display'):
            self.log_display.empty()
    
    def reset_for_new_session(self):
        """Reset all counters and logs for a new analysis session"""
        # Reset metrics counters
        self.total_processed = 0
        self.successful = 0
        self.failed = 0
        self.skipped = 0
        
        # Reset tracking data
        self.logged_events.clear()
        self.log_messages.clear()
        self.element_status.clear()
        
        # Clear session state for clean start
        if 'displayed_log_uuids' in st.session_state:
            st.session_state.displayed_log_uuids.clear()
        if 'accumulated_log_text' in st.session_state:
            st.session_state.accumulated_log_text = ""
        
        # Update display to show reset metrics
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
    
    def log_timeout(self, element_id: str, timeout_duration: float) -> bool:
        """Log element timeout - guaranteed single entry"""
        # Check if already timed out
        if self.element_status.get(element_id) == "timeout":
            return False  # Already logged
        
        # Update status
        self.element_status[element_id] = "timeout"
        self.failed += 1
        
        # Add log message
        message = f"⏰ {element_id} timed out ({timeout_duration:.1f}s)"
        return self._add_log_message(message, element_id, "timeout")
    
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