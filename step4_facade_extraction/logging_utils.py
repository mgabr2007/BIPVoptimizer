"""
Structured logging utilities for facade extraction module.
"""

import sys
import json
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime
from loguru import logger
from contextlib import contextmanager


class StructuredLogger:
    """Structured logger with context management for facade extraction."""
    
    def __init__(self, project_id: Optional[int] = None, step: str = "step4_facade"):
        self.project_id = project_id
        self.step = step
        self.context: Dict[str, Any] = {}
        self._setup_logger()
    
    def _setup_logger(self):
        """Setup loguru logger with structured format."""
        # Remove default handler
        logger.remove()
        
        # Add console handler with structured format
        logger.add(
            sys.stdout,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
                   "<level>{level: <8}</level> | "
                   "<cyan>{extra[project_id]}</cyan> | "
                   "<cyan>{extra[step]}</cyan> | "
                   "<level>{message}</level>",
            level="INFO",
            colorize=True,
            backtrace=True,
            diagnose=True
        )
        
        # Add file handler for persistent logging
        log_file = Path("logs") / f"facade_extraction_{datetime.now().strftime('%Y%m%d')}.log"
        log_file.parent.mkdir(exist_ok=True)
        
        logger.add(
            log_file,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {extra[project_id]} | {extra[step]} | {message}",
            level="DEBUG",
            rotation="1 day",
            retention="30 days",
            compression="zip"
        )
        
        # Bind default context
        self.logger = logger.bind(
            project_id=self.project_id or "unknown",
            step=self.step
        )
    
    def add_context(self, **kwargs):
        """Add context to logger."""
        self.context.update(kwargs)
        self.logger = self.logger.bind(**kwargs)
    
    def info(self, message: str, **extra):
        """Log info message with context."""
        self.logger.bind(**extra).info(message)
    
    def warning(self, message: str, **extra):
        """Log warning message with context."""
        self.logger.bind(**extra).warning(message)
    
    def error(self, message: str, **extra):
        """Log error message with context."""
        self.logger.bind(**extra).error(message)
    
    def debug(self, message: str, **extra):
        """Log debug message with context."""
        self.logger.bind(**extra).debug(message)
    
    def success(self, message: str, **extra):
        """Log success message with context."""
        self.logger.bind(**extra).success(message)
    
    def log_operation_start(self, operation: str, **metadata):
        """Log operation start."""
        self.info(f"Starting {operation}", operation=operation, **metadata)
    
    def log_operation_end(self, operation: str, success: bool, duration: float, **metadata):
        """Log operation completion."""
        level = "success" if success else "error"
        status = "completed" if success else "failed"
        getattr(self, level)(
            f"Operation {operation} {status} in {duration:.2f}s",
            operation=operation,
            success=success,
            duration=duration,
            **metadata
        )
    
    def log_data_processing(self, total_rows: int, processed_rows: int, errors: int):
        """Log data processing progress."""
        self.info(
            f"Data processing: {processed_rows}/{total_rows} rows, {errors} errors",
            total_rows=total_rows,
            processed_rows=processed_rows,
            errors=errors,
            progress_pct=round((processed_rows / total_rows) * 100, 1) if total_rows > 0 else 0
        )
    
    def log_database_operation(self, operation: str, table: str, rows_affected: int):
        """Log database operation."""
        self.info(
            f"Database {operation} on {table}: {rows_affected} rows affected",
            db_operation=operation,
            table=table,
            rows_affected=rows_affected
        )
    
    def log_validation_results(self, total_elements: int, valid_elements: int, errors: int):
        """Log validation results."""
        self.info(
            f"Validation completed: {valid_elements}/{total_elements} valid, {errors} errors",
            total_elements=total_elements,
            valid_elements=valid_elements,
            validation_errors=errors,
            validation_rate=round((valid_elements / total_elements) * 100, 1) if total_elements > 0 else 0
        )


@contextmanager
def log_operation(logger_instance: StructuredLogger, operation: str, **metadata):
    """Context manager for logging operations with timing."""
    start_time = datetime.now()
    logger_instance.log_operation_start(operation, **metadata)
    
    try:
        yield logger_instance
        duration = (datetime.now() - start_time).total_seconds()
        logger_instance.log_operation_end(operation, True, duration, **metadata)
    except Exception as e:
        duration = (datetime.now() - start_time).total_seconds()
        logger_instance.log_operation_end(operation, False, duration, error=str(e), **metadata)
        raise


class LogViewer:
    """Log viewer for Streamlit UI."""
    
    def __init__(self, max_lines: int = 100):
        self.max_lines = max_lines
        self.log_file = Path("logs") / f"facade_extraction_{datetime.now().strftime('%Y%m%d')}.log"
    
    def get_recent_logs(self) -> list:
        """Get recent log entries."""
        if not self.log_file.exists():
            return []
        
        try:
            with open(self.log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                return lines[-self.max_lines:] if len(lines) > self.max_lines else lines
        except Exception as e:
            return [f"Error reading log file: {str(e)}"]
    
    def filter_logs(self, project_id: Optional[int] = None, level: Optional[str] = None) -> list:
        """Filter logs by project_id and/or level."""
        logs = self.get_recent_logs()
        
        if project_id is not None:
            logs = [log for log in logs if str(project_id) in log]
        
        if level is not None:
            logs = [log for log in logs if level.upper() in log]
        
        return logs


# Global logger instance
_logger_instance: Optional[StructuredLogger] = None


def get_logger(project_id: Optional[int] = None, step: str = "step4_facade") -> StructuredLogger:
    """Get or create logger instance."""
    global _logger_instance
    
    if _logger_instance is None or _logger_instance.project_id != project_id:
        _logger_instance = StructuredLogger(project_id, step)
    
    return _logger_instance


def setup_error_monitoring():
    """Setup error monitoring (placeholder for Sentry integration)."""
    # TODO: Integrate with Sentry or similar service
    # import sentry_sdk
    # sentry_sdk.init(dsn="your-sentry-dsn")
    pass