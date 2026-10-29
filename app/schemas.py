from datetime import datetime

from pydantic import BaseModel, Field, HttpUrl


class LinkCreate(BaseModel):
    url: HttpUrl = Field(max_length=2048)


class LinkResponse(BaseModel):
    short_code: str
    short_url: str
    original_url: str
    expires_at: datetime
