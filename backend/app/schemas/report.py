"""
Report generation schemas.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict
from pydantic import field_validator


class ReportGenerateRequest(BaseModel):
    """Request model for generating a report."""
    
    visit_id: str = Field(..., description="Screening visit identifier")
    format: str = Field(default="PDF", description="Report format (PDF/JSON)")
    
    @field_validator("format")
    @classmethod
    def validate_format(cls, v: str) -> str:
        """Validate report format."""
        v = v.upper()
        if v not in ["PDF", "JSON"]:
            raise ValueError("Format must be either 'PDF' or 'JSON'")
        return v
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "visit_id": "550e8400-e29b-41d4-a716-446655440002",
                "format": "PDF"
            }
        }
    )


class ReportResponse(BaseModel):
    """Response model for report metadata."""
    
    report_id: str = Field(..., description="Report identifier")
    visit_id: str = Field(..., description="Screening visit identifier")
    patient_id: str = Field(..., description="Patient identifier")
    patient_name: str = Field(..., description="Patient's full name")
    format: str = Field(..., description="Report format")
    file_path: str = Field(..., description="Path to stored report")
    file_size_bytes: Optional[str] = Field(None, description="File size")
    generated_at: datetime = Field(..., description="Generation timestamp")
    download_count: int = Field(..., description="Number of downloads")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "report_id": "550e8400-e29b-41d4-a716-446655440007",
                "visit_id": "550e8400-e29b-41d4-a716-446655440002",
                "patient_id": "550e8400-e29b-41d4-a716-446655440001",
                "patient_name": "John Doe",
                "format": "PDF",
                "file_path": "reports/2024/01/15/report_550e8400.pdf",
                "file_size_bytes": "245760",
                "generated_at": "2024-01-15T10:35:00Z",
                "download_count": 0
            }
        }
    )


class ReportDownloadResponse(BaseModel):
    """Response model for report download."""
    
    report_id: str = Field(..., description="Report identifier")
    file_path: str = Field(..., description="Path to report file")
    file_name: str = Field(..., description="Downloadable file name")
    content_type: str = Field(..., description="MIME type")
    file_size_bytes: int = Field(..., description="File size in bytes")


ReportGenerateRequest.model_rebuild()