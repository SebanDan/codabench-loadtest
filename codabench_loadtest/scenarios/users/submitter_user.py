from __future__ import annotations

from time import sleep
from typing import TYPE_CHECKING

from locust import HttpUser, between, tag, task
from pydantic import SecretStr

from codabench_loadtest.clients import get_custom_codabench_locust_client

if TYPE_CHECKING:
    from codabench_loadtest.models import SubmissionZip, User


class SubmitterUser(HttpUser):
    """Uploads a code submission to the competition."""

    wait_time = between(1, 3)

    def on_start(self):
        user: User = self.environment.user_pool.get_random_user()
        self.codabench_client = get_custom_codabench_locust_client(
            client=self.client,
            settings=self.environment.codabench_settings,
            update={"username": user.username, "password": SecretStr(user.password)},
        )
        self.codabench_client.login()

    def on_stop(self):
        """Register the submission IDs uploaded during the test to the environment for later cleanup."""
        self.environment.env_setup.dataset_ids.extend(
            self.codabench_client.list_dataset_ids(kind="submission")
        )

    def _submit(
        self,
        submission_zip: SubmissionZip,
        *,
        custom_name: str = "",
        wait_for_completion: bool = True,
    ):
        data = self.codabench_client.upload_submission(
            self.environment.competition_id,
            zip_bytes=submission_zip.get_zip_bytes(),
            zip_name=submission_zip.zip_name,
            size=submission_zip.bytes_size(),
        )
        submission = self.codabench_client.create_submission(
            data["key"],
            phase=self.environment.competition_phase_id,
            name=submission_zip.zip_name + custom_name,
        )
        if wait_for_completion:
            self.codabench_client.poll_until_done(
                self.codabench_client.get_submission, submission["id"]
            )
        return submission

    @tag("normal")
    @task
    def submit_task(self):
        submission_zip: SubmissionZip = (
            self.environment.submission_pool.get_random_submission_zip()
        )
        self._submit(submission_zip)

    @tag("clumsy")
    @task
    def clumsy_submit_task(self):
        submission_zip: SubmissionZip = (
            self.environment.submission_pool.get_random_submission_zip()
        )
        first = self._submit(
            submission_zip,
            custom_name="+clumsy_first_submit",
            wait_for_completion=False,
        )
        self.codabench_client.cancel_submission(first["id"])
        sleep(2.5)
        self._submit(submission_zip, custom_name="+clumsy_second_submit")

    @tag("heavy")
    @task
    def heavy_submit_task(self):
        submission_zip: SubmissionZip = (
            self.environment.submission_pool.get_random_submission_zip()
        )
        submission_zip.generate_heavy_space(extra_size_mb=1024, chunk_mb=50)
        self._submit(submission_zip, custom_name="+heavy_submit")
