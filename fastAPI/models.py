from pydantic import BaseModel

class FontRequest(BaseModel):
    font_name: str

class S3ImageRequest(BaseModel):
    url: str