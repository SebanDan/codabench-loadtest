from locust import between, tag, task

from codabench_loadtest.scenarios.tasks.base_user import BaseUser


class SmokeUser(BaseUser):
    """A user that performs a smoke test of the codabench platform."""

    wait_time = between(1, 2)

    def on_start(self):
        self.codabench_client = self.get_codabench_client()
        self.codabench_client.login()

    @tag("normal")
    @task
    def smoke_task(self):
        self.client.get("/api/my_profile/")
        self.client.get("/api/competitions/")
        self.client.get("/api/competitions/front_page/")
        self.client.get("/api/leaderboards/")
