from typing import TYPE_CHECKING

from locust import HttpUser, between, tag, task
from pydantic import SecretStr

from codabench_loadtest.clients import get_custom_codabench_locust_client

if TYPE_CHECKING:
    from codabench_loadtest.models import User


class SmokeUser(HttpUser):
    wait_time = between(1, 2)

    def on_start(self):
        user: User = self.environment.user_pool.get_random_user()
        self.codabench_client = get_custom_codabench_locust_client(
            client=self.client,
            settings=self.environment.codabench_settings,
            update={"username": user.username, "password": SecretStr(user.password)},
        )
        self.codabench_client.login()

    @tag("normal")
    @task
    def smoke_task(self):
        self.client.get("/api/my_profile/")
        self.client.get("/api/competitions/")
        self.client.get("/api/competitions/front_page/")
        self.client.get("/api/leaderboards/")
