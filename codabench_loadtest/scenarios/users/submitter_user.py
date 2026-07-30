from __future__ import annotations

from time import sleep
from typing import TYPE_CHECKING

from locust import HttpUser, between, tag, task

from codabench_loadtest.clients.base_api_client import FAILED
from codabench_loadtest.clients.exceptions import LoadTestError
from codabench_loadtest.scenarios.tasks.common import BaseUser

if TYPE_CHECKING:
    from codabench_loadtest.models import CompetitionZip, SubmissionZip


class SubmitterUser(BaseUser, HttpUser):
    """A user that submits tasks to the codabench platform."""

    wait_time = between(1, 3)

    def on_start(self):
        self.codabench_client = self.get_codabench_client()
        self.codabench_client.login()

    def on_stop(self):
        """Register the submission IDs uploaded during the test to the environment for later cleanup."""
        self.environment.env_setup.dataset_ids.extend(
            self.codabench_client.list_dataset_ids(kind="submission")
        )

    def _submit(
        self,
        competition: CompetitionZip,
        submission_zip: SubmissionZip,
        *,
        custom_name: str = "",
        wait_for_completion: bool = True,
    ):
        try:
            request_name = f"{competition.name} {submission_zip.zip_name} {custom_name}"
            data = self.codabench_client.upload_submission(
                competition.id,  # type: ignore
                zip_bytes=submission_zip.get_zip_bytes(),
                zip_name=submission_zip.zip_name,
                size=submission_zip.bytes_size(),
                custom_name=request_name,
            )
            submission = self.codabench_client.create_submission(
                data["key"],
                phase=competition.get_phase_id(),
                name=request_name,
            )
            if wait_for_completion:
                self.codabench_client.poll_until_done(
                    self.codabench_client.get_submission, submission["id"]
                )
            self.raise_on_submission_failure(submission_id=submission["id"])
            return submission
        except LoadTestError as e:
            print(f"Error during submission: {e}")
            return submission

    def raise_on_submission_failure(self, submission_id: int):
        submission = self.codabench_client.get_submission(submission_id)
        if submission["status"] == FAILED:
            raise LoadTestError(
                f"Submission {submission_id} failed with message: {submission['message']}"
            )

    @tag("normal")
    @task
    def submit_task(self):

        competition_zip: CompetitionZip = (
            self.environment.competition_pool.get_random_competition()
        )
        submission_zip: SubmissionZip = competition_zip.get_random_submission_zip()
        self._submit(competition=competition_zip, submission_zip=submission_zip)

    @tag("clumsy")
    @task
    def clumsy_submit_task(self):
        competition_zip: CompetitionZip = (
            self.environment.competition_pool.get_random_competition()
        )
        submission_zip: SubmissionZip = competition_zip.get_random_submission_zip()
        first = self._submit(
            competition=competition_zip,
            submission_zip=submission_zip,
            custom_name="+clumsy_first_submit",
            wait_for_completion=False,
        )
        self.codabench_client.cancel_submission(first["id"])
        sleep(2.5)
        self._submit(
            competition=competition_zip,
            submission_zip=submission_zip,
            custom_name="+clumsy_second_submit",
        )

    @tag("heavy")
    @task
    def heavy_submit_task(self):
        competition_zip: CompetitionZip = (
            self.environment.competition_pool.get_random_competition()
        )
        submission_zip: SubmissionZip = competition_zip.get_random_submission_zip()
        submission_zip.generate_heavy_space(extra_size_mb=1024, chunk_mb=50)
        self._submit(
            competition=competition_zip,
            submission_zip=submission_zip,
            custom_name="+heavy_submit",
        )
