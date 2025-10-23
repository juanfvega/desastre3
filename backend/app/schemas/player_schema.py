from pydantic import BaseModel
from typing import Optional

class PlayerIn(BaseModel):
    username: str
    birthdate: Optional[str] = None
    avatar: Optional[str] = None

class PlayerOut(BaseModel):
    id: str
    username: str
    birthdate: Optional[str] = None
    avatar: Optional[str] = None