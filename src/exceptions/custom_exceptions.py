"""
Custom Exception Classes for WhatsApp Auto-Agent
===============================================

This module defines all custom exceptions used throughout the application.
Each exception provides specific context for different types of errors,
making debugging and error handling more precise and informative.
"""

class WhatsAppAgentError(Exception):
    """
    Base exception class for all WhatsApp Agent related errors.
    
    This serves as the parent class for all custom exceptions in the application,
    providing a common interface for error handling and allowing for broad
    exception catching when needed.
    """
    def __init__(self, message: str, error_code: str = None):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)

class ConfigurationError(WhatsAppAgentError):
    """
    Raised when there are issues with configuration files or settings.
    
    This exception is thrown when:
    - Config files are missing or corrupted
    - Required environment variables are not set
    - Invalid configuration values are provided
    """
    pass

class BrowserError(WhatsAppAgentError):
    """
    Raised when browser automation encounters problems.
    
    Common scenarios include:
    - WebDriver initialization failures
    - Browser crashes or timeouts
    - Element not found or interaction failures
    - WhatsApp Web login issues
    """
    pass

class MessageProcessingError(WhatsAppAgentError):
    """
    Raised when message processing fails.
    
    This covers:
    - Failed message parsing
    - Contact identification issues
    - Reply generation failures
    - Message sending errors
    """
    pass

class APIError(WhatsAppAgentError):
    """
    Raised when external API calls fail.
    
    Handles:
    - OpenAI/Clarifai API failures
    - Network connectivity issues
    - Authentication problems
    - API rate limiting (handled separately)
    """
    pass

class RateLimitError(APIError):
    """
    Specific exception for API rate limiting scenarios.
    
    This exception includes retry information and helps implement
    exponential backoff strategies for API calls.
    """
    def __init__(self, message: str, retry_after: int = None):
        super().__init__(message)
        self.retry_after = retry_after
