"""
Pydantic models for API requests and responses
"""

from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


# Request Models

class ChatRequest(BaseModel):
    """Chat request model"""
    message: str
    session_id: Optional[str] = None
    security_enabled: Optional[bool] = True


class UploadResponse(BaseModel):
    """Document upload response"""
    status: str
    document_id: str
    filename: str
    extracted_length: int
    extraction_method: str
    preview: str
    message: str


# Response Models

class DocumentInfo(BaseModel):
    """Document information model"""
    id: str
    title: str
    content: str
    owner_id: Optional[str] = None
    content_length: int
    upload_date: str


class ChatResponse(BaseModel):
    """Chat response model"""
    response: str
    session_id: str
    sources: Optional[List[str]] = None


class UserInfo(BaseModel):
    """User information model"""
    authenticated: bool
    name: Optional[str] = None
    id: Optional[str] = None
    email: Optional[str] = None


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    configuration: str
    foundry_configured: bool
    search_configured: bool
    timestamp: datetime
