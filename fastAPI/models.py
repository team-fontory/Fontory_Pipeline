import fastAPI.config as config
from pydantic import BaseModel, Field

class FontRequest(BaseModel):
    font_name: str = Field(..., alias=config.FONT_NAME_KEY)
    member_id: int = Field(..., alias=config.MEMBER_ID_KEY)
    font_id: int = Field(..., alias=config.FONT_ID_KEY)
    template_url: str = Field(..., alias=config.TEMPLATE_URL_KEY)
    author: str = Field(..., alias=config.AUTHOR_KEY)
    request_uuid: str = Field(..., alias=config.REQUEST_UUID_KEY)