"""
WhatsApp Auto-Agent Package
==========================

A comprehensive AI-powered WhatsApp automation system that provides:
- Intelligent message processing and responses
- Contact-based filtering and skip lists
- Async operations for better performance
- Comprehensive logging and error handling
- Modular architecture for easy maintenance

Author: Your Name
Version: 1.0.0
License: MIT
"""

__version__ = "1.0.0"
__author__ = "Your Name"
__license__ = "MIT"

# Package-level imports for easier access
from .core.whatsapp_handler import WhatsAppHandler
from .core.reply_generator import ReplyGenerator
from .core.config_manager import ConfigManager
from .core.logger_manager import LoggerManager

__all__ = [
    "WhatsAppHandler",
    "ReplyGenerator", 
    "ConfigManager",
    "LoggerManager"
]
