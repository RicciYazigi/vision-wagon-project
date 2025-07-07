from enum import Enum

class ContentType(Enum):
    TEXT = "text"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
    DOCUMENT = "document"
    PRESENTATION = "presentation"
    WEBSITE = "website"
    SOCIAL_POST = "social_post"

class GenerationStatus(Enum):
    PENDING = "pending"
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"


