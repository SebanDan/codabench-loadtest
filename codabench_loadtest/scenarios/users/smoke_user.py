from locust import HttpUser, between, tag, task

from codabench_loadtest.scenarios.utils import authenticate
from codabench_loadtest.common import CodabenchClient

class SmokeUser(HttpUser):
    wait_time = between(1, 2)

    def on_start(self):
        user = self.environment.user_pool.get_random_user()
        authenticate(self.client, user.username, user.password)

    @tag("normal")
    @task
    def smoke_task(self):
        self.client.get("/api/my_profile/")
        self.client.get("/api/competitions/")
        self.client.get("/api/competitions/front_page/")
        self.client.get("/api/leaderboards/")
