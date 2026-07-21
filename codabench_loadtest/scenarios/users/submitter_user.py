from locust import HttpUser, between, task

from codabench_loadtest.scenarios.utils import (
    authenticate,
    create_submission,
    upload_submission,
    validate_submission_zip,
)


class SubmitterUser(HttpUser):
    """Uploads a code submission to the competition."""

    wait_time = between(1, 3)

    def on_start(self):
        user = self.environment.user_pool.get_random_user()
        authenticate(self.client, user.username, user.password)

        submission_zip = self.environment.data_dir / "mini_MNIST_code_submission.zip"
        validate_submission_zip(submission_zip)
        self._zip_bytes = submission_zip.read_bytes()
        self._zip_name = submission_zip.name

    @task
    def submit(self):
        data = upload_submission(
            self.client,
            self.environment.competition_id,
            self._zip_bytes,
            self._zip_name,
        )
        create_submission(self.client, data["key"], phase=0)
