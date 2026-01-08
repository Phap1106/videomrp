from pydantic import BaseModel, Field
from typing import Optional, Literal

class JobCreate(BaseModel):
    title: str = ""
    source_url: str = Field(default="")
    target_lang: str = "vi"
    clip_seconds: int = 0
    style_preset: Literal["standard", "viral", "meme", "cinematic"] = "standard"
    subtitles: bool = True
    voiceover: bool = False
    make_shorts: bool = False

class JobOut(BaseModel):
    id: str
    title: str
    status: str
    progress: float
    current_step: str
    error_message: str = ""
    created_at: str
    updated_at: str
    processed_filename: Optional[str] = None
