"""
Response formatting utilities for consistent API responses.
"""

from typing import Any, Dict, List, Optional, Union
from datetime import datetime, timezone


def create_success_response(
    data: Any,
    message: str = "Success",
    status_code: int = 200
) -> Dict[str, Any]:
    """
    Create a standardized success response.
    
    Args:
        data: Response data
        message: Success message
        status_code: HTTP status code
        
    Returns:
        Formatted response dictionary
    """
    return {
        "success": True,
        "message": message,
        "status_code": status_code,
        "data": data,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def create_error_response(
    error: str,
    message: str,
    status_code: int = 400,
    detail: Optional[Any] = None
) -> Dict[str, Any]:
    """
    Create a standardized error response.
    
    Args:
        error: Error code
        message: Error message
        status_code: HTTP status code
        detail: Additional error details
        
    Returns:
        Formatted error response dictionary
    """
    response = {
        "success": False,
        "error": error,
        "message": message,
        "status_code": status_code,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    
    if detail is not None:
        response["detail"] = detail
    
    return response


def create_paginated_response(
    items: List[Any],
    total: int,
    page: int,
    page_size: int,
    message: str = "Success"
) -> Dict[str, Any]:
    """
    Create a standardized paginated response.
    
    Args:
        items: List of items for current page
        total: Total number of items
        page: Current page number
        page_size: Items per page
        
    Returns:
        Formatted paginated response
    """
    total_pages = (total + page_size - 1) // page_size if total > 0 else 1
    
    return {
        "success": True,
        "message": message,
        "data": {
            "items": items,
            "pagination": {
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_previous": page > 1,
            }
        },
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }