from __future__ import annotations

from faker import Faker
from pydantic import BaseModel, Field


class User(BaseModel):
    username: str = Field(default_factory=lambda: Faker().user_name())
    password: str = Field(default_factory=lambda: Faker().password())
    email: str | None = Field(default_factory=lambda: Faker().email())


class UserPool(BaseModel):
    pool_type: str = Field(default="default")
    users: list[User] = Field(default_factory=list)
