from __future__ import annotations

from time import sleep
from typing import TYPE_CHECKING

from locust import HttpUser, between, task

from codabench_loadtest.scenarios.utils import (
    authenticate,
    cancel_submission,
    create_submission,
    re_run_submission,
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

    def _submit(self, submission_zip: SubmissionZip, phase: int = 0):
        data = upload_submission(
            self.client,
            self.environment.competition_id,
            zip_bytes=submission_zip.get_zip_bytes(),
            zip_name=submission_zip.zip_name,
            size=submission_zip.bytes_size(),
        )
        return create_submission(self.client, data["key"], phase=phase)

    @task
    def submit_task(self):
        submission_zip: SubmissionZip = (
            self.environment.submission_pool.get_random_submission_zip()
        )
        self._submit(submission_zip)

    @task
    def clumsy_submit(self):
        submission_zip: SubmissionZip = (
            self.environment.submission_pool.get_random_submission_zip()
        )
        first = self._submit(submission_zip)
        cancel_submission(self.client, first["id"])
        sleep(1.75)
        self._submit(submission_zip)
        re_run_submission(self.client, first["id"])

    @task
    def heavy_submit(self):
        submission_zip: SubmissionZip = (
            self.environment.submission_pool.get_random_submission_zip()
        )
        submission_zip.generate_heavy_space(extra_size_mb=1024, chunk_mb=50)
        self._submit(submission_zip)
