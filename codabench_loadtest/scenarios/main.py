from locust import HttpUser, between, task


class CodabenchSmokeUser(HttpUser):
    wait_time = between(1, 2)
    token = None

    def on_start(self):
        response = self.client.post(
            "/api/api-token-auth/", json={"username": "admin", "password": "12345"}
        )
        self.client.headers.update(
            {"Authorization": f"Token {response.json()['token']}"}
        )

    @task
    def smoke_task(self):
        self.client.get("/api/my_profile/")
        self.client.get("/api/analytics/users_usage/")
