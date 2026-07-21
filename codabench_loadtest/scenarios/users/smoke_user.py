from locust import HttpUser, between, task

from codabench_loadtest.scenarios.utils import authenticate


class SmokeUser(HttpUser):
    wait_time = between(1, 2)

    def on_start(self):
        user = self.environment.user_pool.get_random_user()
        print(user)
        authenticate(self.client, user.username, user.password)

    @task
    def smoke_task(self):
        self.client.get("/api/my_profile/")
        self.client.get("/api/competitions/")
        self.client.get("/api/competitions/front_page/")
        self.client.get("/api/leaderboards/")
