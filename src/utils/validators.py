"""
Validation Functions
===================

This module provides validation functions for various data types and formats
used throughout the WhatsApp Auto-Agent application. These validators ensure
data integrity and help prevent errors by validating inputs before processing.
"""

import re
import os
import json
from typing import Dict, Any, Optional, List
from pathlib import Path

def validate_phone_number(phone: str) -> bool:
    """
    Validate phone number format.
    
    Checks if the provided phone number follows international format
    and contains only valid characters. Supports various international formats.
    
    Args:
        phone (str): Phone number string to validate
        
    Returns:
        bool: True if phone number is valid, False otherwise
        
    Examples:
        >>> validate_phone_number("+1234567890")
        True
        >>> validate_phone_number("invalid-phone")
        False
    """
    if not phone or not isinstance(phone, str):
        return False
    
    # Remove all whitespace and common separators
    cleaned_phone = re.sub(r'[\s\-\(\)\.]', '', phone)
    
    # Check international format: optional + followed by 7-15 digits
    pattern = r'^\+?[1-9]\d{6,14}$'
    
    return bool(re.match(pattern, cleaned_phone))

def validate_message_content(message: str, max_length: int = 1000) -> tuple[bool, str]:
    """
    Validate message content for safety and format compliance.
    
    Performs comprehensive validation including:
    - Length limits
    - Content safety checks
    - Character encoding validation
    - Spam pattern detection
    
    Args:
        message (str): Message content to validate
        max_length (int): Maximum allowed message length
        
    Returns:
        tuple[bool, str]: (is_valid, error_message)
    """
    if not message:
        return False, "Message cannot be empty"
    
    if not isinstance(message, str):
        return False, "Message must be a string"
    
    # Check length limits
    if len(message) > max_length:
        return False, f"Message exceeds maximum length of {max_length} characters"
    
    # Check for null bytes or control characters that might cause issues
    if '\x00' in message or any(ord(char) < 32 and char not in '\t\n\r' for char in message):
        return False, "Message contains invalid control characters"
    
    # Basic spam pattern detection
    spam_patterns = [
        r'(.)\1{10,}',  # Repeated characters (10+ times)
        r'[A-Z]{20,}',  # Excessive capitals
        r'www\.[a-zA-Z0-9\-]+\.[a-zA-Z]{2,}',  # URLs (might want to restrict)
    ]
    
    for pattern in spam_patterns:
        if re.search(pattern, message):
            return False, "Message appears to contain spam patterns"
    
    return True, ""

def validate_api_key(api_key: str, key_type: str = "openai") -> bool:
    """
    Validate API key format for different services.
    
    Checks if the API key follows the expected format for the specified service.
    This helps catch configuration errors early.
    
    Args:
        api_key (str): API key to validate
        key_type (str): Type of API key ("openai", "clarifai")
        
    Returns:
        bool: True if API key format is valid
    """
    if not api_key or not isinstance(api_key, str):
        return False
    
    # Remove any whitespace
    api_key = api_key.strip()
    
    if key_type.lower() == "openai":
        # OpenAI keys typically start with 'sk-' and are 51 characters
        return api_key.startswith('sk-') and len(api_key) == 51
    
    elif key_type.lower() == "clarifai":
        # Clarifai keys are typically 32 character hex strings
        return len(api_key) == 32 and all(c in '0123456789abcdef' for c in api_key.lower())
    
    # Generic validation for unknown key types
    return len(api_key) >= 20 and api_key.isalnum()

def validate_config_file(config_path: str) -> tuple[bool, str, Optional[Dict[Any, Any]]]:
    """
    Validate configuration file existence, format, and required fields.
    
    Performs comprehensive validation of configuration files including:
    - File existence and readability
    - JSON format validation
    - Required field presence
    - Value type checking
    
    Args:
        config_path (str): Path to configuration file
        
    Returns:
        tuple[bool, str, Optional[Dict]]: (is_valid, error_message, config_data)
    """
    try:
        # Check if file exists and is readable
        if not os.path.exists(config_path):
            return False, f"Configuration file not found: {config_path}", None
        
        if not os.access(config_path, os.R_OK):
            return False, f"Configuration file is not readable: {config_path}", None
        
        # Try to load and parse JSON
        with open(config_path, 'r', encoding='utf-8') as f:
            config_data = json.load(f)
        
        # Validate required sections
        required_sections = ['bot_settings', 'ai_settings', 'browser_settings']
        for section in required_sections:
            if section not in config_data:
                return False, f"Missing required section: {section}", None
        
        # Validate critical settings
        bot_settings = config_data.get('bot_settings', {})
        required_bot_fields = ['name', 'auto_reply_enabled', 'fallback_message']
        
        for field in required_bot_fields:
            if field not in bot_settings:
                return False, f"Missing required bot setting: {field}", None
        
        return True, "", config_data
    
    except json.JSONDecodeError as e:
        return False, f"Invalid JSON format: {str(e)}", None
    except Exception as e:
        return False, f"Configuration validation error: {str(e)}", None

def validate_skip_list(skip_list_data: Dict[str, Any]) -> tuple[bool, List[str]]:
    """
    Validate skip list data structure and content.
    
    Ensures skip list contains valid data and follows expected format.
    
    Args:
        skip_list_data (Dict): Skip list configuration data
        
    Returns:
        tuple[bool, List[str]]: (is_valid, list_of_errors)
    """
    errors = []
    
    if not isinstance(skip_list_data, dict):
        errors.append("Skip list must be a dictionary")
        return False, errors
    
    # Check required sections
    if 'skip_contacts' not in skip_list_data:
        errors.append("Missing 'skip_contacts' section")
    
    skip_contacts = skip_list_data.get('skip_contacts', {})
    
    # Validate phone numbers in skip list
    phone_list = skip_contacts.get('by_phone', [])
    if phone_list:
        for phone in phone_list:
            if not validate_phone_number(phone):
                errors.append(f"Invalid phone number in skip list: {phone}")
    
    # Validate names list
    name_list = skip_contacts.get('by_name', [])
    if name_list and not all(isinstance(name, str) and name.strip() for name in name_list):
        errors.append("Invalid names in skip list - must be non-empty strings")
    
    return len(errors) == 0, errors

def validate_browser_config(browser_config: Dict[str, Any]) -> tuple[bool, str]:
    """
    Validate browser configuration settings.
    
    Checks browser-related configuration for valid values and types.
    
    Args:
        browser_config (Dict): Browser configuration dictionary
        
    Returns:
        tuple[bool, str]: (is_valid, error_message)
    """
    required_fields = ['implicit_wait', 'explicit_wait', 'retry_attempts']
    
    for field in required_fields:
        if field not in browser_config:
            return False, f"Missing required browser config field: {field}"
        
        value = browser_config[field]
        if not isinstance(value, (int, float)) or value <= 0:
            return False, f"Browser config '{field}' must be a positive number"
    
    # Validate timeout values are reasonable
    if browser_config.get('implicit_wait', 0) > 60:
        return False, "Implicit wait should not exceed 60 seconds"
    
    if browser_config.get('explicit_wait', 0) > 120:
        return False, "Explicit wait should not exceed 120 seconds"
    
    return True, ""
