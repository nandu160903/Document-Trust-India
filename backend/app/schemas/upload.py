"""Pydantic schemas for the document upload API."""

from pydantic import BaseModel, Field


class UploadResponse(BaseModel):
    """Successful upload response payload."""

    status: str = Field(default="success", examples=["success"])
    filename: str = Field(..., description="UUID-based stored filename")
    original_filename: str = Field(..., description="Client-provided original name")
    path: str = Field(..., description="Absolute path of the saved file")
    content_type: str = Field(..., description="Validated MIME type")
