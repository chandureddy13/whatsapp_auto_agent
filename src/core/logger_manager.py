"""
Advanced Logging Management System
=================================

This module provides comprehensive logging functionality for the WhatsApp Auto-Agent.
It implements structured logging with multiple handlers, log rotation, and different
log levels for various components of the application.

Features:
- Colored console output for better readability
- File-based logging with automatic rotation
- Chat-specific logging for message tracking
- Performance metrics logging
- Error tracking and notification system
"""

import os
import logging
import logging.handlers
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
import json
import csv
from dataclasses import dataclass, asdict
import colorlog
from rich.console import Console
from rich.logging import RichHandler

from ..exceptions.custom_exceptions import ConfigurationError


@dataclass
class ChatLogEntry:
    """
    Data structure for chat log entries.
    
    Standardizes the format for logging chat interactions with all
    necessary metadata for analysis and debugging.
    """
    timestamp: str
    contact_name: str
    phone_number: str
    incoming_message: str
    outgoing_message: str
    response_type: str  # 'ai', 'template', 'fallback'
    processing_time: float
    message_id: str
    session_id: str
    error: Optional[str] = None


class LoggerManager:
    """
    Centralized logging management system.
    
    Provides multiple types of logging including:
    - Application logging (info, debug, error)
    - Chat interaction logging
    - Performance metrics logging
    - Security event logging
    
    Implements proper log rotation and formatting for production use.
    """
    
    def __init__(self, log_directory: str = None):
        """
        Initialize the logging manager.
        
        Args:
            log_directory (str, optional): Custom log directory path
        """
        # Set up paths
        self.base_path = Path(__file__).parent.parent.parent
        self.log_dir = Path(log_directory) if log_directory else self.base_path / "logs"
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Log file paths
        self.app_log_file = self.log_dir / "bot.log"
        self.chat_log_file = self.log_dir / "chat_interactions.csv"
        self.error_log_file = self.log_dir / "errors.log"
        self.performance_log_file = self.log_dir / "performance.log"
        
        # Initialize console for rich output
        self.console = Console()
        
        # Set up loggers
        self._setup_application_logger()
        self._setup_chat_logger()
        self._setup_error_logger()
        self._setup_performance_logger()
        
        # Initialize chat log CSV if it doesn't exist
        self._initialize_chat_log_csv()
    
    def _setup_application_logger(self) -> None:
        """
        Set up the main application logger with console and file handlers.
        
        Configures colored console output and rotating file handler for
        general application logging.
        """
        self.app_logger = logging.getLogger('whatsapp_agent')
        self.app_logger.setLevel(logging.DEBUG)
        
        # Prevent duplicate handlers
        if self.app_logger.handlers:
            self.app_logger.handlers.clear()
        
        # Console handler with colors
        console_handler = RichHandler(
            console=self.console,
            show_time=True,
            show_path=False,
            markup=True
        )
        console_handler.setLevel(logging.INFO)
        
        # File handler with rotation
        file_handler = logging.handlers.RotatingFileHandler(
            self.app_log_file,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        
        # Formatters
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%H:%M:%S'
        )
        
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        console_handler.setFormatter(console_formatter)
        file_handler.setFormatter(file_formatter)
        
        self.app_logger.addHandler(console_handler)
        self.app_logger.addHandler(file_handler)
    
    def _setup_chat_logger(self) -> None:
        """
        Set up dedicated logger for chat interactions.
        
        Creates a separate logger specifically for tracking chat messages
        and responses for analysis and debugging purposes.
        """
        self.chat_logger = logging.getLogger('chat_interactions')
        self.chat_logger.setLevel(logging.INFO)
        
        if self.chat_logger.handlers:
            self.chat_logger.handlers.clear()
        
        # Chat log file handler
        chat_handler = logging.handlers.RotatingFileHandler(
            self.log_dir / "chat_log.log",
            maxBytes=50*1024*1024,  # 50MB
            backupCount=10,
            encoding='utf-8'
        )
        
        chat_formatter = logging.Formatter(
            '%(asctime)s - CHAT - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        chat_handler.setFormatter(chat_formatter)
        self.chat_logger.addHandler(chat_handler)
        
        # Prevent propagation to root logger
        self.chat_logger.propagate = False
    
    def _setup_error_logger(self) -> None:
        """
        Set up dedicated error logger for tracking failures and exceptions.
        
        Maintains a separate log file specifically for errors to facilitate
        debugging and monitoring system health.
        """
        self.error_logger = logging.getLogger('error_tracking')
        self.error_logger.setLevel(logging.ERROR)
        
        if self.error_logger.handlers:
            self.error_logger.handlers.clear()
        
        error_handler = logging.handlers.RotatingFileHandler(
            self.error_log_file,
            maxBytes=25*1024*1024,  # 25MB
            backupCount=5,
            encoding='utf-8'
        )
        
        error_formatter = logging.Formatter(
            '%(asctime)s - ERROR - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d\n'
            'Message: %(message)s\n'
            '%(exc_info)s\n' + '-'*80,
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        error_handler.setFormatter(error_formatter)
        self.error_logger.addHandler(error_handler)
        self.error_logger.propagate = False
    
    def _setup_performance_logger(self) -> None:
        """
        Set up performance metrics logger.
        
        Tracks performance metrics like response times, API call durations,
        and system resource usage for optimization purposes.
        """
        self.perf_logger = logging.getLogger('performance')
        self.perf_logger.setLevel(logging.INFO)
        
        if self.perf_logger.handlers:
            self.perf_logger.handlers.clear()
        
        perf_handler = logging.handlers.RotatingFileHandler(
            self.performance_log_file,
            maxBytes=20*1024*1024,  # 20MB
            backupCount=3,
            encoding='utf-8'
        )
        
        perf_formatter = logging.Formatter(
            '%(asctime)s - PERF - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        perf_handler.setFormatter(perf_formatter)
        self.perf_logger.addHandler(perf_handler)
        self.perf_logger.propagate = False
    
    def _initialize_chat_log_csv(self) -> None:
        """
        Initialize CSV file for structured chat logging.
        
        Creates CSV file with proper headers if it doesn't exist.
        This provides structured data for analysis and reporting.
        """
        if not self.chat_log_file.exists():
            headers = [
                'timestamp', 'contact_name', 'phone_number', 'incoming_message',
                'outgoing_message', 'response_type', 'processing_time',
                'message_id', 'session_id', 'error'
            ]
            
            with open(self.chat_log_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(headers)
    
    def info(self, message: str, extra: Dict[str, Any] = None) -> None:
        """
        Log info level message.
        
        Args:
            message (str): Log message
            extra (Dict[str, Any], optional): Additional context data
        """
        if extra:
            message = f"{message} | Extra: {json.dumps(extra, default=str)}"
        self.app_logger.info(message)
    
    def debug(self, message: str, extra: Dict[str, Any] = None) -> None:
        """
        Log debug level message.
        
        Args:
            message (str): Log message
            extra (Dict[str, Any], optional): Additional context data
        """
        if extra:
            message = f"{message} | Extra: {json.dumps(extra, default=str)}"
        self.app_logger.debug(message)
    
    def warning(self, message: str, extra: Dict[str, Any] = None) -> None:
        """
        Log warning level message.
        
        Args:
            message (str): Log message
            extra (Dict[str, Any], optional): Additional context data
        """
        if extra:
            message = f"{message} | Extra: {json.dumps(extra, default=str)}"
        self.app_logger.warning(message)
    
    def error(self, message: str, exception: Exception = None, extra: Dict[str, Any] = None) -> None:
        """
        Log error level message with optional exception details.
        
        Args:
            message (str): Error message
            exception (Exception, optional): Exception object for traceback
            extra (Dict[str, Any], optional): Additional context data
        """
        error_context = {"error_message": message}
        if extra:
            error_context.update(extra)
        
        log_message = f"{message} | Context: {json.dumps(error_context, default=str)}"
        
        if exception:
            self.app_logger.error(log_message, exc_info=exception)
            self.error_logger.error(log_message, exc_info=exception)
        else:
            self.app_logger.error(log_message)
            self.error_logger.error(log_message)
    
    def critical(self, message: str, exception: Exception = None, extra: Dict[str, Any] = None) -> None:
        """
        Log critical level message for severe errors.
        
        Args:
            message (str): Critical error message
            exception (Exception, optional): Exception object
            extra (Dict[str, Any], optional): Additional context data
        """
        critical_context = {"critical_error": message, "timestamp": datetime.now().isoformat()}
        if extra:
            critical_context.update(extra)
        
        log_message = f"CRITICAL: {message} | Context: {json.dumps(critical_context, default=str)}"
        
        if exception:
            self.app_logger.critical(log_message, exc_info=exception)
            self.error_logger.critical(log_message, exc_info=exception)
        else:
            self.app_logger.critical(log_message)
            self.error_logger.critical(log_message)
    
    def log_chat_interaction(self, chat_entry: ChatLogEntry) -> None:
        """
        Log chat interaction to both structured CSV and text log.
        
        Args:
            chat_entry (ChatLogEntry): Structured chat log entry
        """
        try:
            # Log to CSV for structured analysis
            with open(self.chat_log_file, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([
                    chat_entry.timestamp,
                    chat_entry.contact_name,
                    chat_entry.phone_number,
                    chat_entry.incoming_message[:500] + '...' if len(chat_entry.incoming_message) > 500 else chat_entry.incoming_message,
                    chat_entry.outgoing_message[:500] + '...' if len(chat_entry.outgoing_message) > 500 else chat_entry.outgoing_message,
                    chat_entry.response_type,
                    chat_entry.processing_time,
                    chat_entry.message_id,
                    chat_entry.session_id,
                    chat_entry.error or ''
                ])
            
            # Log to text file for readability
            log_message = (
                f"Chat with {chat_entry.contact_name} ({chat_entry.phone_number}) | "
                f"Type: {chat_entry.response_type} | "
                f"Time: {chat_entry.processing_time:.2f}s | "
                f"ID: {chat_entry.message_id}"
            )
            
            if chat_entry.error:
                log_message += f" | Error: {chat_entry.error}"
            
            self.chat_logger.info(log_message)
            
        except Exception as e:
            self.error(f"Failed to log chat interaction: {str(e)}", e)
    
    def log_performance_metric(self, metric_name: str, value: float, unit: str = "ms", context: Dict[str, Any] = None) -> None:
        """
        Log performance metrics for monitoring and optimization.
        
        Args:
            metric_name (str): Name of the performance metric
            value (float): Metric value
            unit (str): Unit of measurement
            context (Dict[str, Any], optional): Additional context
        """
        metric_data = {
            "metric": metric_name,
            "value": value,
            "unit": unit,
            "timestamp": datetime.now().isoformat()
        }
        
        if context:
            metric_data["context"] = context
        
        self.perf_logger.info(json.dumps(metric_data))
    
    def log_security_event(self, event_type: str, details: Dict[str, Any]) -> None:
        """
        Log security-related events for monitoring and alerting.
        
        Args:
            event_type (str): Type of security event
            details (Dict[str, Any]): Event details and context
        """
        security_data = {
            "event_type": event_type,
            "timestamp": datetime.now().isoformat(),
            "details": details
        }
        
        self.app_logger.warning(f"SECURITY EVENT: {event_type} | {json.dumps(security_data)}")
        self.error_logger.warning(f"SECURITY: {json.dumps(security_data)}")
    
    def get_log_stats(self) -> Dict[str, Any]:
        """
        Get logging statistics and file information.
        
        Returns:
            Dict[str, Any]: Log file statistics and information
        """
        stats = {}
        
        log_files = [
            ("app_log", self.app_log_file),
            ("chat_log", self.chat_log_file), 
            ("error_log", self.error_log_file),
            ("performance_log", self.performance_log_file)
        ]
        
        for log_name, log_path in log_files:
            if log_path.exists():
                stat = log_path.stat()
                stats[log_name] = {
                    "size_bytes": stat.st_size,
                    "size_mb": round(stat.st_size / (1024*1024), 2),
                    "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    "exists": True
                }
            else:
                stats[log_name] = {"exists": False}
        
        return stats
    
    def cleanup_old_logs(self, days_to_keep: int = 30) -> None:
        """
        Clean up log files older than specified days.
        
        Args:
            days_to_keep (int): Number of days to retain log files
        """
        try:
            import time
            current_time = time.time()
            cutoff_time = current_time - (days_to_keep * 24 * 60 * 60)
            
            cleaned_files = []
            
            for log_file in self.log_dir.glob("*.log*"):
                if log_file.stat().st_mtime < cutoff_time:
                    log_file.unlink()
                    cleaned_files.append(str(log_file))
            
            if cleaned_files:
                self.info(f"Cleaned up {len(cleaned_files)} old log files", {"files": cleaned_files})
            
        except Exception as e:
            self.error(f"Failed to cleanup old logs: {str(e)}", e)
    
    def create_chat_log_entry(
        self,
        contact_name: str,
        phone_number: str,
        incoming_message: str,
        outgoing_message: str,
        response_type: str,
        processing_time: float,
        message_id: str,
        session_id: str,
        error: str = None
    ) -> ChatLogEntry:
        """
        Create a standardized chat log entry.
        
        Args:
            contact_name (str): Name of the contact
            phone_number (str): Phone number of the contact
            incoming_message (str): Received message
            outgoing_message (str): Sent response
            response_type (str): Type of response generated
            processing_time (float): Time taken to process
            message_id (str): Unique message identifier
            session_id (str): Session identifier
            error (str, optional): Error message if any
            
        Returns:
            ChatLogEntry: Structured chat log entry
        """
        return ChatLogEntry(
            timestamp=datetime.now().isoformat(),
            contact_name=contact_name,
            phone_number=phone_number,
            incoming_message=incoming_message,
            outgoing_message=outgoing_message,
            response_type=response_type,
            processing_time=processing_time,
            message_id=message_id,
            session_id=session_id,
            error=error
        )
    
    def __del__(self):
        """
        Cleanup when logger manager is destroyed.
        
        Ensures all handlers are properly closed and resources are freed.
        """
        try:
            # Close all handlers
            for logger in [self.app_logger, self.chat_logger, self.error_logger, self.perf_logger]:
                for handler in logger.handlers[:]:
                    handler.close()
                    logger.removeHandler(handler)
        except:
            pass  # Ignore errors during cleanup
