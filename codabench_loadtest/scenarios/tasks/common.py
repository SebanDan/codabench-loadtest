from __future__ import annotations

from typing import TYPE_CHECKING

from locust import HttpUser, tag, task
from pydantic import SecretStr

from codabench_loadtest.clients import get_custom_codabench_locust_client

if TYPE_CHECKING:
    from codabench_loadtest.clients import CodabenchLocustClient
    from codabench_loadtest.models import User


class BaseUser(HttpUser):
    """A base user class that provides common functionality for all user types."""

    abstract = True
    codabench_client: CodabenchLocustClient
    _logged_in: bool = False

    def get_codabench_client(self) -> CodabenchLocustClient:
        codabench_user: User = self.environment.user_pool.get_random_user()
        return get_custom_codabench_locust_client(
            client=self.client,
            settings=self.environment.codabench_settings,
            update={
                "username": codabench_user.username,
                "password": SecretStr(codabench_user.password),
            },
        )

    @task
    @tag("health")
    def environement_health_check(self):
        self.client.get("/api/my_profile/")
