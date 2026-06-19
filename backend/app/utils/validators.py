"""
Validation utilities for input sanitization and validation.
"""

import re
from typing import Optional, Any
from uuid import UUID


def validate_email(email: str) -> bool:
    """
    Validate email address format.
    
    Args:
        email: Email address to validate
        
    Returns:
        True if valid, False otherwise
    """
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(email_pattern, email))


def validate_phone(phone: str) -> bool:
    """
    Validate phone number format.
    
    Args:
        phone: Phone number to validate
        
    Returns:
        True if valid, False otherwise
    """
    # Remove common separators
    cleaned = re.sub(r'[\s\-\(\)\+]', '', phone)
    return bool(re.match(r'^[0-9]{7,15}$', cleaned))


def validate_national_id(national_id: str) -> bool:
    """
    Validate national ID format.
    
    Args:
        national_id: National ID to validate
        
    Returns:
        True if valid, False otherwise
    """
    # Alphanumeric with possible hyphens
    return bool(re.match(r'^[A-Za-z0-9\-]{5,20}$', national_id))


def sanitize_input(value: str) -> str:
    """
    Sanitize input string to prevent XSS and injection.
    
    Args:
        value: String to sanitize
        
    Returns:
        Sanitized string
    """
    if not value:
        return ""
    
    # Remove HTML tags
    cleaned = re.sub(r'<[^>]+>', '', value)
    
    # Remove dangerous characters
    cleaned = re.sub(r'[;\'"]', '', cleaned)
    
    # Trim whitespace
    return cleaned.strip()


def is_valid_uuid(value: str) -> bool:
    """
    Check if a string is a valid UUID.
    
    Args:
        value: String to check
        
    Returns:
        True if valid UUID, False otherwise
    """
    try:
        UUID(value)
        return True
    except (ValueError, TypeError):
        return False


def validate_required_fields(data: dict, required_fields: list) -> Optional[list]:
    """
    Validate that all required fields are present and non-empty.
    
    Args:
        data: Dictionary to validate
        required_fields: List of required field names
        
    Returns:
        List of missing fields, or None if all present
    """
    missing = []
    for field in required_fields:
        value = data.get(field)
        if value is None or (isinstance(value, str) and not value.strip()):
            missing.append(field)
    return missing if missing else None


def validate_range(value: Any, min_val: Any, max_val: Any) -> bool:
    """
    Validate that a value is within a range.
    
    Args:
        value: Value to validate
        min_val: Minimum allowed value
        max_val: Maximum allowed value
        
    Returns:
        True if within range, False otherwise
    """
    try:
        return min_val <= value <= max_val
    except TypeError:
        return False


def validate_enum(value: Any, allowed_values: list) -> bool:
    """
    Validate that a value is in an allowed set.
    
    Args:
        value: Value to validate
        allowed_values: List of allowed values
        
    Returns:
        True if allowed, False otherwise
    """
    return value in allowed_values


def truncate_string(value: str, max_length: int, suffix: str = "...") -> str:
    """
    Truncate a string to a maximum length.
    
    Args:
        value: String to truncate
        max_length: Maximum length
        suffix: Suffix to add when truncated
        
    Returns:
        Truncated string
    """
    if len(value) <= max_length:
        return value
    return value[:max_length - len(suffix)] + suffix