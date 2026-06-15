"""
Clinical note schemas for free-text observations.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict
from pydantic import field_validator


class ClinicalNoteCreateRequest(BaseModel):
    """Request model for creating a clinical note."""
    
    title: Optional[str] = Field(None, max_length=255, description="Note title")
    content: str = Field(..., min_length=1, max_length=5000, description="Note content")
    note_type: str = Field(default="GENERAL", description="Note type (GENERAL/FOLLOW_UP/REFERRAL)")
    is_urgent: str = Field(default="NO", description="Urgency flag (NO/YES/CRITICAL)")
    
    @classmethod
    @field_validator("note_type")
    def validate_note_type(cls, v: str) -> str:
        """Validate note type."""
        allowed = ["GENERAL", "FOLLOW_UP", "REFERRAL"]
        if v not in allowed:
            raise ValueError(f"Note type must be one of {allowed}")
        return v
    
    @classmethod
    @field_validator("is_urgent")
    def validate_is_urgent(cls, v: str) -> str:
        """Validate urgency flag."""
        allowed = ["NO", "YES", "CRITICAL"]
        if v not in allowed:
            raise ValueError(f"Urgency flag must be one of {allowed}")
        return v
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "title": "Initial Consultation",
                "content": "Patient presents with increased thirst and frequent urination. No previous diabetes diagnosis.",
                "note_type": "GENERAL",
                "is_urgent": "NO"
            }
        }
    )


class ClinicalNoteUpdateRequest(BaseModel):
    """Request model for updating a clinical note."""
    
    title: Optional[str] = Field(None, max_length=255, description="Note title")
    content: Optional[str] = Field(None, min_length=1, max_length=5000, description="Note content")
    note_type: Optional[str] = Field(None, description="Note type")
    is_urgent: Optional[str] = Field(None, description="Urgency flag")


class ClinicalNoteResponse(BaseModel):
    """Response model for clinical note."""
    
    note_id: str = Field(..., description="Note identifier")
    patient_id: str = Field(..., description="Patient identifier")
    patient_name: str = Field(..., description="Patient's full name")
    visit_id: Optional[str] = Field(None, description="Associated screening visit")
    author_id: Optional[str] = Field(None, description="Author identifier")
    author_name: Optional[str] = Field(None, description="Author's full name")
    title: Optional[str] = Field(None, description="Note title")
    content: str = Field(..., description="Note content")
    note_type: str = Field(..., description="Note type")
    is_urgent: str = Field(..., description="Urgency flag")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "note_id": "550e8400-e29b-41d4-a716-446655440006",
                "patient_id": "550e8400-e29b-41d4-a716-446655440001",
                "patient_name": "John Doe",
                "visit_id": None,
                "author_id": "550e8400-e29b-41d4-a716-446655440000",
                "author_name": "Dr. Jane Smith",
                "title": "Initial Consultation",
                "content": "Patient presents with increased thirst...",
                "note_type": "GENERAL",
                "is_urgent": "NO",
                "created_at": "2024-01-15T10:30:00Z",
                "updated_at": "2024-01-15T10:30:00Z"
            }
        }
    )


class ClinicalNoteListResponse(BaseModel):
    """Response model for clinical note list."""
    
    note_id: str = Field(..., description="Note identifier")
    title: Optional[str] = Field(None, description="Note title")
    note_type: str = Field(..., description="Note type")
    is_urgent: str = Field(..., description="Urgency flag")
    created_at: datetime = Field(..., description="Creation timestamp")
    author_name: Optional[str] = Field(None, description="Author's full name")


ClinicalNoteCreateRequest.model_rebuild()