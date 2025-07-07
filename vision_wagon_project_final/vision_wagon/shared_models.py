from dataclasses import dataclass
from typing import Dict, Any, Optional, List
from datetime import datetime
from .shared_enums import ContentType, GenerationStatus

@dataclass
class GeneratedContent:
    content_id: str
    content_type: ContentType
    title: str
    description: str
    content_data: Any
    created_at: datetime = datetime.utcnow()
    file_path: Optional[str] = None
    size_bytes: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None
    dimensions: Optional[tuple] = None  # For images/videos (width, height)
    duration: Optional[float] = None  # For audio/video (seconds)
    thumbnail: Optional[str] = None # Path to thumbnail image

@dataclass
class ContentRequest:
    request_id: str
    content_type: ContentType
    prompt: str
    created_at: datetime = datetime.utcnow()
    parameters: Dict[str, Any] = None
    style_guide: Optional[Dict[str, Any]] = None
    brand_guidelines: Optional[Dict[str, Any]] = None
    target_audience: Optional[str] = None
    platform: Optional[str] = None
    status: GenerationStatus = GenerationStatus.PENDING
    error: Optional[str] = None
    completed_at: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None


