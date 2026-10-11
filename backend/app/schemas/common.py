"""
Common and shared schema definitions across the API.
"""

from datetime import datetime
from typing import Any, List, Optional
from pydantic import BaseModel, Field


class ErrorDetail(BaseModel):
    """
    Standardized error payload wrapper.
    """

    code: str = Field(description="Machine-readable error classification code")
    message: str = Field(description="Human-readable explanation of the error")
    details: Optional[Any] = Field(default=None, description="Detailed field-level context or diagnostics")
    timestamp: datetime = Field(description="UTC timestamp of error occurrence")


class ErrorResponse(BaseModel):
    """
    Root error response wrapper schema.
    """

    error: ErrorDetail
