"""
File handling utility functions.
"""

import os
import shutil
from pathlib import Path
from typing import Union, Optional
from datetime import datetime
import uuid


def ensure_directory_exists(directory_path: Union[str, Path]) -> Path:
    """
    Ensure a directory exists, creating it if necessary.
    
    Args:
        directory_path: Path to directory
        
    Returns:
        Path object for the directory
    """
    path = Path(directory_path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_file_size(file_path: Union[str, Path]) -> int:
    """
    Get file size in bytes.
    
    Args:
        file_path: Path to file
        
    Returns:
        File size in bytes, or 0 if file doesn't exist
    """
    path = Path(file_path)
    if path.exists():
        return path.stat().st_size
    return 0


def delete_file(file_path: Union[str, Path]) -> bool:
    """
    Delete a file if it exists.
    
    Args:
        file_path: Path to file
        
    Returns:
        True if deleted, False if file didn't exist
    """
    path = Path(file_path)
    if path.exists():
        try:
            path.unlink()
            return True
        except OSError:
            return False
    return False


def get_file_extension(file_path: Union[str, Path]) -> str:
    """
    Get file extension without the dot.
    
    Args:
        file_path: Path to file
        
    Returns:
        File extension (e.g., 'pdf', 'txt')
    """
    return Path(file_path).suffix.lstrip('.')


def generate_filename(
    prefix: str = "",
    extension: str = "pdf",
    include_timestamp: bool = True,
    include_uuid: bool = True
) -> str:
    """
    Generate a unique filename.
    
    Args:
        prefix: Optional prefix for the filename
        extension: File extension (without dot)
        include_timestamp: Whether to include timestamp
        include_uuid: Whether to include UUID
        
    Returns:
        Generated filename
    """
    parts = []
    
    if prefix:
        parts.append(prefix)
    
    if include_timestamp:
        parts.append(datetime.now().strftime("%Y%m%d_%H%M%S"))
    
    if include_uuid:
        parts.append(str(uuid.uuid4())[:8])
    
    name = "_".join(parts) if parts else str(uuid.uuid4())
    return f"{name}.{extension.lstrip('.')}"


def get_unique_file_path(directory: Union[str, Path], filename: str) -> Path:
    """
    Get a unique file path, adding a suffix if the file exists.
    
    Args:
        directory: Directory path
        filename: Desired filename
        
    Returns:
        Unique file path
    """
    directory = Path(directory)
    ensure_directory_exists(directory)
    
    file_path = directory / filename
    
    # If file exists, add a numeric suffix
    if file_path.exists():
        base_name = file_path.stem
        extension = file_path.suffix
        counter = 1
        
        while True:
            new_name = f"{base_name}_{counter}{extension}"
            new_path = directory / new_name
            if not new_path.exists():
                return new_path
            counter += 1
    
    return file_path


def copy_file(source: Union[str, Path], destination: Union[str, Path]) -> Path:
    """
    Copy a file with proper error handling.
    
    Args:
        source: Source file path
        destination: Destination file path
        
    Returns:
        Path to copied file
        
    Raises:
        FileNotFoundError: If source doesn't exist
        OSError: If copy fails
    """
    source_path = Path(source)
    if not source_path.exists():
        raise FileNotFoundError(f"Source file not found: {source}")
    
    destination_path = Path(destination)
    ensure_directory_exists(destination_path.parent)
    
    shutil.copy2(source_path, destination_path)
    return destination_path


def read_file_content(file_path: Union[str, Path], binary: bool = False) -> Union[str, bytes]:
    """
    Read file content.
    
    Args:
        file_path: Path to file
        binary: Whether to read as binary
        
    Returns:
        File content as string or bytes
        
    Raises:
        FileNotFoundError: If file doesn't exist
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    mode = 'rb' if binary else 'r'
    with open(path, mode) as f:
        return f.read()


def write_file_content(
    file_path: Union[str, Path],
    content: Union[str, bytes],
    binary: bool = False
) -> Path:
    """
    Write content to a file.
    
    Args:
        file_path: Path to file
        content: Content to write
        binary: Whether to write as binary
        
    Returns:
        Path to written file
    """
    path = Path(file_path)
    ensure_directory_exists(path.parent)
    
    mode = 'wb' if binary else 'w'
    with open(path, mode) as f:
        f.write(content)
    
    return path