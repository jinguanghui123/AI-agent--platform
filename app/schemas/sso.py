from pydantic import BaseModel
from typing import Optional

class SSOAuthorizeResponse(BaseModel):
    url: str
    state: str

class SSOCallbackRequest(BaseModel):
    code: str
    state: str

class SSOUserInfo(BaseModel):
    email: Optional[str] = None
    name: Optional[str] = None
    preferred_username: Optional[str] = None
    sub: Optional[str] = None