from __future__ import annotations
from pydantic import BaseModel, Field

class User(BaseModel):
    username: str
    password: str

class UserPool(BaseModel):
    users: list[User] = Field(default_factory=list)