from locust import HttpUser, between, task

from codabench_loadtest.scenarios.utils import (
    authenticate,
    create_submission,
    upload_submission,
    validate_submission_zip,
)


class ClumsyUser(HttpUser):
    """A user that is not very good at using the platform."""

    wait_time = between(1, 3)

    def on_start(self):
        user = self.environment.user_pool.get_random_user()
        authenticate(self.client, user.username, user.password)

    @task
    def clumsy_task(self): ...
