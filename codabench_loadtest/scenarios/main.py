import os
from pathlib import Path

from locust import HttpUser, between, task
from locust.clients import HttpSession
from locust.exception import StopUser

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

USERNAME = os.environ.get("CODABENCH_USERNAME", "admin")
PASSWORD = os.environ.get("CODABENCH_PASSWORD", "12345")


def _authenticate(client: HttpSession):
    response = client.post(
        "/api/api-token-auth/", json={"username": USERNAME, "password": PASSWORD}
    )
    response.raise_for_status()
    client.headers.update({"Authorization": f"Token {response.json()['token']}"})


class CodabenchSmokeUser(HttpUser):
    wait_time = between(1, 2)

    def on_start(self):
        _authenticate(self.client)

    @task
    def smoke_task(self):
        self.client.get("/api/my_profile/")
        self.client.get("/api/analytics/users_usage/")


class MnistSubmissionUser(HttpUser):
    """Uploads a code submission to the MNIST competition.

    Each iteration reproduces the 4 steps the web UI performs:
      1. POST /api/datasets/            -> reserve a slot and get a presigned upload URL
      2. PUT  <sassy_url>               -> upload the zip to object storage
      3. PUT  /api/datasets/completed/  -> tell the backend the upload is done
      4. POST /api/submissions/         -> create the submission on the phase

    Run several of these users concurrently to check that simultaneous
    submissions on the MNIST competition are accepted.
    """

    wait_time = between(1, 3)

    competition_search = os.environ.get("MNIST_COMPETITION_SEARCH", "MNIST")
    submission_zip = Path(
        os.environ.get(
            "SUBMISSION_ZIP", str(DATA_DIR / "mini_MNIST_code_submission.zip")
        )
    )

    def on_start(self):
        _authenticate(self.client)

        if not self.submission_zip.is_file():
            raise StopUser(f"Submission zip not found: {self.submission_zip}")
        self._zip_bytes = self.submission_zip.read_bytes()
        self._zip_name = self.submission_zip.name

        self.competition_id = (
            os.environ.get("MNIST_COMPETITION_ID") or self._find_competition()
        )
        self.phase_id = os.environ.get("MNIST_PHASE_ID") or self._find_phase(
            self.competition_id
        )

    def _find_competition(self):
        response = self.client.get(
            "/api/competitions/",
            params={"search": self.competition_search},
            name="/api/competitions/ [search]",
        )
        payload = response.json()
        items = (
            payload.get("results", payload) if isinstance(payload, dict) else payload
        )
        for competition in items:
            title = (competition.get("title") or "").lower()
            if self.competition_search.lower() in title:
                return competition["id"]
        if items:
            return items[0]["id"]
        raise StopUser(f"No competition matching '{self.competition_search}' found")

    def _find_phase(self, competition_id):
        response = self.client.get(
            f"/api/competitions/{competition_id}/",
            name="/api/competitions/[id]/",
        )
        phases = response.json().get("phases", [])
        if not phases:
            raise StopUser(f"Competition {competition_id} has no phase")
        index = int(os.environ.get("MNIST_PHASE_INDEX", "0"))
        return phases[index]["id"]

    @task
    def submit(self):
        # 1. Reserve a submission dataset slot and get the presigned upload URL.
        metadata = {
            "type": "submission",
            "competition": self.competition_id,
            "request_sassy_file_name": self._zip_name,
            "file_name": self._zip_name,
            "file_size": len(self._zip_bytes),
        }
        with self.client.post(
            "/api/datasets/",
            json=metadata,
            name="/api/datasets/ [create submission]",
            catch_response=True,
        ) as response:
            if response.status_code != 201:
                response.failure(
                    f"dataset create failed: {response.status_code} {response.text[:200]}"
                )
                return
            data = response.json()
            key = data["key"]
            sassy_url = data["sassy_url"]

        # 2. Upload the zip to object storage (presigned URL, no auth header).
        with self.client.put(
            sassy_url,
            data=self._zip_bytes,
            headers={"Authorization": None, "Content-Type": "application/zip"},
            name="PUT [storage upload]",
            catch_response=True,
        ) as response:
            if response.status_code not in (200, 201, 204):
                response.failure(f"storage upload failed: {response.status_code}")
                return

        # 3. Notify the backend that the upload is complete.
        with self.client.put(
            f"/api/datasets/completed/{key}/",
            name="/api/datasets/completed/[key]/",
            catch_response=True,
        ) as response:
            if response.status_code not in (200, 201, 204):
                response.failure(f"dataset completion failed: {response.status_code}")
                return

        # 4. Create the submission on the phase.
        submission = {
            "data": key,
            "phase": int(self.phase_id),
            "tasks": [],
            "organization": None,
        }
        with self.client.post(
            "/api/submissions/",
            json=submission,
            name="/api/submissions/ [create]",
            catch_response=True,
        ) as response:
            if response.status_code not in (200, 201):
                response.failure(
                    f"submission failed: {response.status_code} {response.text[:200]}"
                )
