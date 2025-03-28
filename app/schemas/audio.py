from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class AudioBase(BaseModel):
    original_filename: str
    file_path: str # Relative path for retrieval info

class AudioCreate(BaseModel):
    # Input for creation might just be the file itself + name via form data
    pass

class AudioUpdate(BaseModel):
    # Update allows to rename
    original_filename: Optional[str] = None

class AudioInDBBase(AudioBase):
    id: int
    user_id: int
    created_at: datetime
    content_type: Optional[str] = None
    stored_filename: str

    class Config:
        from_attributes = True

class Audio(AudioInDBBase):
    pass # API response model