"""
Global Element Processing Registry
Prevents element duplication across all levels of the application
"""

import threading
from datetime import datetime
from typing import Set, Dict, Tuple, Optional
import streamlit as st

class GlobalElementRegistry:
    """
    Thread-safe global registry to prevent element duplication
    """
    
    def __init__(self):
        self.processing_elements: Dict[str, datetime] = {}
        self.completed_elements: Dict[str, datetime] = {}
        self.failed_elements: Dict[str, datetime] = {}
        self.lock = threading.Lock()
    
    def start_processing(self, element_id: str) -> Tuple[bool, str]:
        """
        Register element as processing
        
        Args:
            element_id: Unique element identifier
            
        Returns:
            Tuple of (success, message)
        """
        with self.lock:
            # Check if already processing
            if element_id in self.processing_elements:
                return False, f"Element {element_id} already processing"
            
            # Check if already completed
            if element_id in self.completed_elements:
                return False, f"Element {element_id} already completed"
            
            # Check if already failed
            if element_id in self.failed_elements:
                return False, f"Element {element_id} already failed"
            
            # Register as processing
            self.processing_elements[element_id] = datetime.now()
            return True, f"Element {element_id} registered for processing"
    
    def complete_processing(self, element_id: str) -> Tuple[bool, str]:
        """
        Mark element as completed
        
        Args:
            element_id: Unique element identifier
            
        Returns:
            Tuple of (success, message)
        """
        with self.lock:
            if element_id not in self.processing_elements:
                return False, f"Element {element_id} not in processing"
            
            # Move from processing to completed
            self.completed_elements[element_id] = datetime.now()
            del self.processing_elements[element_id]
            return True, f"Element {element_id} marked as completed"
    
    def fail_processing(self, element_id: str) -> Tuple[bool, str]:
        """
        Mark element as failed
        
        Args:
            element_id: Unique element identifier
            
        Returns:
            Tuple of (success, message)
        """
        with self.lock:
            if element_id not in self.processing_elements:
                return False, f"Element {element_id} not in processing"
            
            # Move from processing to failed
            self.failed_elements[element_id] = datetime.now()
            del self.processing_elements[element_id]
            return True, f"Element {element_id} marked as failed"
    
    def is_processing(self, element_id: str) -> bool:
        """Check if element is currently being processed"""
        with self.lock:
            return element_id in self.processing_elements
    
    def is_completed(self, element_id: str) -> bool:
        """Check if element has been completed"""
        with self.lock:
            return element_id in self.completed_elements
    
    def is_failed(self, element_id: str) -> bool:
        """Check if element has failed"""
        with self.lock:
            return element_id in self.failed_elements
    
    def get_status(self, element_id: str) -> str:
        """Get current status of element"""
        with self.lock:
            if element_id in self.processing_elements:
                return "processing"
            elif element_id in self.completed_elements:
                return "completed"
            elif element_id in self.failed_elements:
                return "failed"
            else:
                return "not_started"
    
    def get_processing_count(self) -> int:
        """Get number of currently processing elements"""
        with self.lock:
            return len(self.processing_elements)
    
    def get_completed_count(self) -> int:
        """Get number of completed elements"""
        with self.lock:
            return len(self.completed_elements)
    
    def get_failed_count(self) -> int:
        """Get number of failed elements"""
        with self.lock:
            return len(self.failed_elements)
    
    def clear(self):
        """Clear all registrations (for new analysis)"""
        with self.lock:
            self.processing_elements.clear()
            self.completed_elements.clear()
            self.failed_elements.clear()
    
    def get_summary(self) -> Dict:
        """Get summary of all registrations"""
        with self.lock:
            return {
                'processing': len(self.processing_elements),
                'completed': len(self.completed_elements),
                'failed': len(self.failed_elements),
                'total': len(self.processing_elements) + len(self.completed_elements) + len(self.failed_elements)
            }

# Global instance
_global_registry = None

def get_global_registry() -> GlobalElementRegistry:
    """Get or create global element registry"""
    global _global_registry
    if _global_registry is None:
        _global_registry = GlobalElementRegistry()
    return _global_registry

def clear_global_registry():
    """Clear global registry (for new analysis)"""
    registry = get_global_registry()
    registry.clear()

def get_registry_summary() -> Dict:
    """Get summary of global registry"""
    registry = get_global_registry()
    return registry.get_summary()