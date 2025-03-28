from pydantic import BaseModel

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class TokenPayload(BaseModel):
    sub: str | None = None # Subject (user identifier, e.g., user ID)
    refresh: bool = False # Is this a refresh token?
    yandex_id: str | None = None # Store Yandex ID in payload for potential refresh logic