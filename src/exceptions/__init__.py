"""
Custom Exception Classes
========================
Centralized exception handling for better error management and debugging.
"""

from .custom_exceptions import (
    WhatsAppAgentError,
    ConfigurationError,
    BrowserError,
    MessageProcessingError,
    APIError,
    RateLimitError
)

__all__ = [
    "WhatsAppAgentError",
    "ConfigurationError", 
    "BrowserError",
    "MessageProcessingError",
    "APIError",
    "RateLimitError"
]
