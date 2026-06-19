"""
JSON handling utility functions.
"""

import json
from typing import Any, Optional, Union
from datetime import datetime, date
from decimal import Decimal


class CustomJSONEncoder(json.JSONEncoder):
    """
    Custom JSON encoder for handling non-serializable types.
    """
    
    def default(self, obj: Any) -> Any:
        if isinstance(obj, datetime):
            return obj.isoformat()
        if isinstance(obj, date):
            return obj.isoformat()
        if isinstance(obj, Decimal):
            return float(obj)
        if hasattr(obj, 'to_dict'):
            return obj.to_dict()
        try:
            return super().default(obj)
        except TypeError:
            return str(obj)


def safe_json_loads(json_str: str, default: Any = None) -> Any:
    """
    Safely load JSON string, returning default on error.
    
    Args:
        json_str: JSON string to parse
        default: Default value on error
        
    Returns:
        Parsed JSON or default
    """
    try:
        return json.loads(json_str)
    except (json.JSONDecodeError, TypeError):
        return default


def safe_json_dumps(
    data: Any,
    indent: Optional[int] = None,
    default: Any = None
) -> str:
    """
    Safely dump data to JSON string.
    
    Args:
        data: Data to serialize
        indent: Indentation level
        default: Default value on error
        
    Returns:
        JSON string or default
    """
    try:
        return json.dumps(data, cls=CustomJSONEncoder, indent=indent)
    except (TypeError, ValueError):
        return json.dumps(default) if default is not None else "null"


def compact_json(data: Any) -> str:
    """
    Convert data to compact JSON (no whitespace).
    
    Args:
        data: Data to serialize
        
    Returns:
        Compact JSON string
    """
    return safe_json_dumps(data, indent=None)


def pretty_json(data: Any) -> str:
    """
    Convert data to pretty-printed JSON.
    
    Args:
        data: Data to serialize
        
    Returns:
        Pretty-printed JSON string
    """
    return safe_json_dumps(data, indent=2)


def json_serialize_datetime(dt: datetime) -> str:
    """
    Serialize datetime to ISO format.
    
    Args:
        dt: Datetime to serialize
        
    Returns:
        ISO format string
    """
    return dt.isoformat()


def parse_json_datetime(json_str: str) -> Optional[datetime]:
    """
    Parse datetime from JSON string.
    
    Args:
        json_str: ISO format datetime string
        
    Returns:
        Datetime object or None
    """
    try:
        return datetime.fromisoformat(json_str.replace('Z', '+00:00'))
    except (ValueError, TypeError):
        return None


def merge_json_objects(obj1: dict, obj2: dict, deep: bool = True) -> dict:
    """
    Merge two JSON objects.
    
    Args:
        obj1: First object (base)
        obj2: Second object (overrides)
        deep: Whether to do deep merge
        
    Returns:
        Merged object
    """
    result = obj1.copy()
    
    for key, value in obj2.items():
        if deep and key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge_json_objects(result[key], value, deep)
        else:
            result[key] = value
    
    return result