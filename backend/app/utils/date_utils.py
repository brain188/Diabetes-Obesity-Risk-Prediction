"""
Date and time utility functions.
"""

from datetime import datetime, date, timedelta, timezone
from typing import Optional, Tuple, Union
import calendar


def calculate_age(birth_date: date) -> int:
    """
    Calculate age from birth date.
    
    Args:
        birth_date: Date of birth
        
    Returns:
        Age in years
    """
    today = date.today()
    return today.year - birth_date.year - (
        (today.month, today.day) < (birth_date.month, birth_date.day)
    )


def format_date(
    dt: Union[datetime, date, str],
    format_str: str = "%Y-%m-%d %H:%M:%S"
) -> str:
    """
    Format a date/datetime object or string.
    
    Args:
        dt: Date/datetime object or string
        format_str: Format string
        
    Returns:
        Formatted date string
    """
    if isinstance(dt, str):
        try:
            dt = datetime.fromisoformat(dt.replace('Z', '+00:00'))
        except ValueError:
            return dt
    
    if isinstance(dt, datetime):
        return dt.strftime(format_str)
    elif isinstance(dt, date):
        return dt.strftime(format_str)
    else:
        return str(dt)


def parse_date(date_str: str, formats: Optional[list] = None) -> Optional[datetime]:
    """
    Parse a date string using multiple formats.
    
    Args:
        date_str: Date string to parse
        formats: List of format strings to try
        
    Returns:
        Parsed datetime object or None
    """
    if formats is None:
        formats = [
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d",
            "%d/%m/%Y %H:%M:%S",
            "%d/%m/%Y",
            "%m/%d/%Y",
            "%Y%m%d",
        ]
    
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    
    return None


def get_date_range(days: int) -> Tuple[datetime, datetime]:
    """
    Get a date range from today going back N days.
    
    Args:
        days: Number of days to go back
        
    Returns:
        Tuple of (start_date, end_date)
    """
    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=days)
    return start_date, end_date


def get_age_category(age: int) -> str:
    """
    Get age category for a given age.
    
    Args:
        age: Age in years
        
    Returns:
        Age category string
    """
    if age < 18:
        return "Under 18"
    elif age < 30:
        return "18-29"
    elif age < 40:
        return "30-39"
    elif age < 50:
        return "40-49"
    elif age < 60:
        return "50-59"
    else:
        return "60+"


def is_date_in_range(
    check_date: Union[datetime, date],
    start_date: Union[datetime, date],
    end_date: Union[datetime, date]
) -> bool:
    """
    Check if a date is within a range.
    
    Args:
        check_date: Date to check
        start_date: Start of range
        end_date: End of range
        
    Returns:
        True if within range, False otherwise
    """
    return start_date <= check_date <= end_date


def get_days_between(start: Union[datetime, date], end: Union[datetime, date]) -> int:
    """
    Get number of days between two dates.
    
    Args:
        start: Start date
        end: End date
        
    Returns:
        Number of days between
    """
    return abs((end - start).days)


def get_week_number(date: Union[datetime, date]) -> int:
    """
    Get ISO week number for a date.
    
    Args:
        date: Date to get week number for
        
    Returns:
        ISO week number
    """
    return date.isocalendar()[1]


def get_month_name(month: int, short: bool = False) -> str:
    """
    Get month name from month number.
    
    Args:
        month: Month number (1-12)
        short: Whether to return short name
        
    Returns:
        Month name
    """
    if short:
        return calendar.month_abbr[month]
    return calendar.month_name[month]