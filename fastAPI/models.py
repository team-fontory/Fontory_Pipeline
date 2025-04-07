from pydantic import BaseModel

class FontRequest(BaseModel):
    font_name: str