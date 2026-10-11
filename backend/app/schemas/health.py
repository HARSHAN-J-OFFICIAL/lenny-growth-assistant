"""
Schema definitions for the system health check endpoints.
"""

from datetime import datetime
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """
    Health diagnostic schema with optional database health probe.
    """

    status: str = Field(default="ok", description="Application service status indicator")
    version: str = Field(description="Running application version")
    timestamp: datetime = Field(description="Current UTC timestamp")
    environment: str = Field(description="Active runtime environment name")
    database: Optional[str] = Field(default=None, description="Database connection status")
    checks: Optional[Dict[str, Any]] = Field(default=None, description="Detailed diagnostic checks")
