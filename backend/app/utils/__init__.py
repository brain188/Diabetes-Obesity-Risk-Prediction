"""
Utils module for helper functions and utilities.
"""

from app.utils.pdf_generator import PDFGenerator
from app.utils.validators import (
    validate_email,
    validate_phone,
    validate_national_id,
    sanitize_input,
    is_valid_uuid,
)
from app.utils.date_utils import (
    calculate_age,
    format_date,
    parse_date,
    get_date_range,
    get_age_category,
)
from app.utils.file_utils import (
    ensure_directory_exists,
    get_file_size,
    delete_file,
    get_file_extension,
    generate_filename,
)
from app.utils.json_utils import (
    safe_json_loads,
    safe_json_dumps,
    compact_json,
    pretty_json,
)

__all__ = [
    "PDFGenerator",
    "validate_email",
    "validate_phone",
    "validate_national_id",
    "sanitize_input",
    "is_valid_uuid",
    "calculate_age",
    "format_date",
    "parse_date",
    "get_date_range",
    "get_age_category",
    "ensure_directory_exists",
    "get_file_size",
    "delete_file",
    "get_file_extension",
    "generate_filename",
    "safe_json_loads",
    "safe_json_dumps",
    "compact_json",
    "pretty_json",
]