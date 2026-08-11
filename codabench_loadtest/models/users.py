from __future__ import annotations

import random

from faker import Faker
from pydantic import BaseModel, Field
import uuid


class User(BaseModel):
    username: str = Field(default_factory=lambda: f"{Faker().user_name()}{uuid.uuid4().hex[:8]}")
    password: str = Field(default_factory=lambda: Faker().password())
    email: str = Field(
        default_factory=lambda: f"{Faker().user_name()}{uuid.uuid4().hex[:8]}@{Faker().free_email_domain()}"
    )
    id: str | None = Field(default=None, description="User ID assigned by the server")


class UserPool(BaseModel):
    pool_type: str = Field(default="default")
    users: list[User] = Field(default_factory=list)

    def get_random_user(self) -> User:
        """
        Get a random user from the pool.
        """
        if not self.users:
            raise ValueError("User pool is empty")
        return random.choice(self.users)
