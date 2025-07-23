"""
Helper Utility Functions
========================

This module contains various utility functions that are used across the application
for common operations like text processing, formatting, and data manipulation.
These functions are designed to be pure (no side effects) and reusable.
"""

import re
import uuid
import random
from datetime import datetime
from typing import Optional, Union, List
import unicodedata

def sanitize_phone_number(phone: str) -> str:
    """
    Clean and standardize phone number format.
    
    This function removes all non-digit characters except '+' at the beginning,
    ensuring consistent phone number formatting for comparison and storage.
    
    Args:
        phone (str): Raw phone number string
        
    Returns:
        str: Cleaned phone number in international format
        
    Examples:
        >>> sanitize_phone_number("+1 (555) 123-4567")
        "+15551234567"
        >>> sanitize_phone_number("555.123.4567")
        "5551234567"
    """
    if not phone:
        return ""
    
    # Remove all characters except digits and leading +
    cleaned = re.sub(r'[^\d+]', '', phone)
    
    # Ensure + is only at the beginning
    if '+' in cleaned:
        parts = cleaned.split('+')
        cleaned = '+' + ''.join(parts[1:])
    
    return cleaned

def format_timestamp(timestamp: Optional[datetime] = None, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    """
    Format datetime object to string representation.
    
    Provides consistent timestamp formatting across the application.
    If no timestamp is provided, uses current time.
    
    Args:
        timestamp (datetime, optional): Datetime object to format
        format_str (str): Format string for datetime formatting
        
    Returns:
        str: Formatted timestamp string
    """
    if timestamp is None:
        timestamp = datetime.now()
    
    return timestamp.strftime(format_str)

def clean_message_text(text: str) -> str:
    """
    Clean and normalize message text for processing.
    
    This function performs several cleaning operations:
    - Removes excessive whitespace
    - Normalizes Unicode characters
    - Strips leading/trailing whitespace
    - Removes or replaces problematic characters
    
    Args:
        text (str): Raw message text
        
    Returns:
        str: Cleaned and normalized text
    """
    if not text:
        return ""
    
    # Normalize Unicode characters (handles accents, special chars)
    text = unicodedata.normalize('NFKD', text)
    
    # Remove excessive whitespace and normalize line breaks
    text = re.sub(r'\s+', ' ', text)
    text = text.strip()
    
    # Remove null bytes and other control characters
    text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text)
    
    return text

def generate_unique_id(prefix: str = "msg") -> str:
    """
    Generate a unique identifier for messages or sessions.
    
    Creates a unique ID combining a prefix with UUID and timestamp,
    useful for tracking messages, sessions, or log entries.
    
    Args:
        prefix (str): Prefix for the generated ID
        
    Returns:
        str: Unique identifier string
        
    Example:
        >>> generate_unique_id("msg")
        "msg_20231215_143022_a1b2c3d4"
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_part = str(uuid.uuid4())[:8]
    return f"{prefix}_{timestamp}_{unique_part}"

def calculate_delay(min_delay: int = 2, max_delay: int = 5) -> float:
    """
    Calculate random delay for human-like response timing.
    
    Generates a random delay within specified bounds to make the bot
    responses appear more natural and avoid detection as automated.
    
    Args:
        min_delay (int): Minimum delay in seconds
        max_delay (int): Maximum delay in seconds
        
    Returns:
        float: Random delay value in seconds
    """
    return round(random.uniform(min_delay, max_delay), 2)

def extract_contact_name(full_contact_info: str) -> str:
    """
    Extract clean contact name from WhatsApp contact information.
    
    WhatsApp Web sometimes provides contact info in various formats.
    This function extracts just the name part for consistent processing.
    
    Args:
        full_contact_info (str): Full contact information string
        
    Returns:
        str: Extracted contact name
    """
    if not full_contact_info:
        return "Unknown"
    
    # Remove common prefixes/suffixes and extra info
    name = full_contact_info.split('(')[0].strip()  # Remove phone in parentheses
    name = name.split(':')[0].strip()  # Remove status info
    name = re.sub(r'\+\d+', '', name).strip()  # Remove phone numbers
    
    return name if name else "Unknown"

def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    Truncate text to specified length with optional suffix.
    
    Useful for logging and display purposes where text length needs to be limited.
    
    Args:
        text (str): Text to truncate
        max_length (int): Maximum allowed length
        suffix (str): Suffix to append if text is truncated
        
    Returns:
        str: Truncated text with suffix if needed
    """
    if not text or len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix

def is_emoji_only(text: str) -> bool:
    """
    Check if text contains only emojis and whitespace.
    
    Useful for determining if a message is just emoji reactions
    and might need different handling.
    
    Args:
        text (str): Text to check
        
    Returns:
        bool: True if text contains only emojis and whitespace
    """
    if not text:
        return False
    
    # Remove whitespace and check if remaining characters are emojis
    clean_text = text.strip()
    if not clean_text:
        return False
    
    # Basic emoji detection using Unicode ranges
    emoji_pattern = re.compile(r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF]+')
    non_emoji_text = emoji_pattern.sub('', clean_text).strip()
    
    return len(non_emoji_text) == 0
