from __future__ import annotations

from time import sleep
from typing import TYPE_CHECKING

from locust import HttpUser, between, tag, task

from codabench_loadtest.scenarios.utils import (
    authenticate,
    cancel_submission,
    create_submission,
    upload_submission,
)

if TYPE_CHECKING:
    from codabench_loadtest.models import SubmissionZip


class SubmitterUser(HttpUser):
    """Uploads a code submission to the competition."""

    wait_time = between(1, 3)

    def on_start(self):
        user = self.environment.user_pool.get_random_user()
        authenticate(self.client, user.username, user.password)

    def _submit(self, submission_zip: SubmissionZip, custom_name: str = ""):
        data = upload_submission(
            self.client,
            self.environment.competition_id,
            zip_bytes=submission_zip.get_zip_bytes(),
            zip_name=submission_zip.zip_name,
            size=submission_zip.bytes_size(),
        )
        submitted = create_submission(
            self.client,
            data["key"],
            phase=self.environment.competition_phase_id,
            name=submission_zip.zip_name + custom_name,
        )
        # wait_submission_completed # :TODO: add a polling method to wait to completion
        return submitted

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
        first = self._submit(submission_zip, custom_name="+clumsy_first_submit")
        cancel_submission(self.client, first["id"])
        sleep(1.75)
        self._submit(submission_zip, custom_name="+clumsy_second_submit")

    @tag("heavy")
    @task
    def heavy_submit_task(self):
        submission_zip: SubmissionZip = (
            self.environment.submission_pool.get_random_submission_zip()
        )
        submission_zip.generate_heavy_space(extra_size_mb=1024, chunk_mb=50)
        self._submit(submission_zip, custom_name="+heavy_submit")
