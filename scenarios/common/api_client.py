from __future__ import annotations

import time
from pathlib import Path
from typing import Any

import requests

from scenarios.common.config import settings

# Submission statuses as returned by the API (Title Case).
SUBMITTING = "Submitting"
SUBMITTED = "Submitted"
PREPARING = "Preparing"
RUNNING = "Running"
SCORING = "Scoring"
CANCELLED = "Cancelled"
FINISHED = "Finished"
FAILED = "Failed"

TERMINAL_STATUSES = frozenset({FINISHED, FAILED, CANCELLED})


class CodabenchClient:
    """Reusable client for the Codabench REST API."""

    def __init__(self, host: str | None = None) -> None:
        self.host = (host or settings.host).rstrip("/")
        self.session = requests.Session()
        self._authenticated = False

    # ------------------------------------------------------------------ auth

    def login(self) -> None:
        settings.require_auth()

        token = settings.api_token.get_secret_value()
        if token:
            self.session.headers["Authorization"] = f"Token {token}"
            self._authenticated = True
            return

        resp = self.session.post(
            f"{self.host}/api/api-token-auth/",
            json={
                "username": settings.username,
                "password": settings.password.get_secret_value(),
            },
        )
        resp.raise_for_status()
        self.session.headers["Authorization"] = f"Token {resp.json()['token']}"
        self._authenticated = True

    def _ensure_auth(self) -> None:
        if not self._authenticated:
            self.login()

    # --------------------------------------------------------- competitions

    def list_competitions(self, **params: Any) -> list[dict[str, Any]]:
        resp = self.session.get(f"{self.host}/api/competitions/", params=params)
        resp.raise_for_status()
        return resp.json()["results"]

    def list_public_competitions(self, **params: Any) -> list[dict[str, Any]]:
        resp = self.session.get(f"{self.host}/api/competitions/public/", params=params)
        resp.raise_for_status()
        return resp.json()["results"]

    def get_front_page(self) -> dict[str, Any]:
        resp = self.session.get(f"{self.host}/api/competitions/front_page/")
        resp.raise_for_status()
        return resp.json()

    def register(self, competition_id: int) -> dict[str, Any]:
        self._ensure_auth()

        resp = self.session.post(
            f"{self.host}/api/competitions/{competition_id}/register/"
        )
        resp.raise_for_status()
        return resp.json()

    # ---------------------------------------------------------- leaderboards

    def get_leaderboard(self, phase_id: int) -> dict[str, Any]:
        resp = self.session.get(f"{self.host}/api/phases/{phase_id}/get_leaderboard/")
        resp.raise_for_status()
        return resp.json()

    # ---------------------------------------------------------- submissions

    def can_make_submission(self, phase_id: int) -> dict[str, Any]:
        self._ensure_auth()

        resp = self.session.get(f"{self.host}/api/can_make_submission/{phase_id}/")
        resp.raise_for_status()
        return resp.json()

    def submit(
        self,
        phase_id: int,
        bundle_path: str | Path,
        *,
        organization: int | None = None,
    ) -> dict[str, Any]:
        self._ensure_auth()

        with open(bundle_path, "rb") as f:
            data: dict[str, Any] = {"phase": phase_id}
            if organization is not None:
                data["organization"] = organization

            resp = self.session.post(
                f"{self.host}/api/submissions/",
                data=data,
                files={"data_file": f},
            )
        resp.raise_for_status()
        return resp.json()

    def get_submission(self, submission_id: int) -> dict[str, Any]:
        resp = self.session.get(f"{self.host}/api/submissions/{submission_id}/")
        resp.raise_for_status()
        return resp.json()

    def get_submission_details(self, submission_id: int) -> dict[str, Any]:
        self._ensure_auth()

        resp = self.session.get(
            f"{self.host}/api/submissions/{submission_id}/get_details/"
        )
        resp.raise_for_status()
        return resp.json()

    def cancel(self, submission_id: int) -> dict[str, Any]:
        self._ensure_auth()

        resp = self.session.get(
            f"{self.host}/api/submissions/{submission_id}/cancel_submission/"
        )
        resp.raise_for_status()
        return resp.json()

    def soft_delete(self, submission_id: int) -> dict[str, Any]:
        self._ensure_auth()

        resp = self.session.delete(
            f"{self.host}/api/submissions/{submission_id}/soft_delete/"
        )
        resp.raise_for_status()
        return resp.json()

    def re_run(
        self, submission_id: int, *, task_key: str | None = None
    ) -> dict[str, Any]:
        self._ensure_auth()

        params: dict[str, str] = {}
        if task_key is not None:
            params["task_key"] = task_key

        resp = self.session.post(
            f"{self.host}/api/submissions/{submission_id}/re_run_submission/",
            params=params,
        )
        resp.raise_for_status()
        return resp.json()

    # ------------------------------------------------------------- polling

    def poll_until_done(
        self,
        submission_id: int,
        *,
        interval: float | None = None,
        timeout: float | None = None,
    ) -> dict[str, Any]:
        interval = interval or settings.poll_interval
        timeout = timeout or settings.poll_timeout
        deadline = time.monotonic() + timeout

        while True:
            result = self.get_submission(submission_id)
            state = result.get("status", "")

            if state in TERMINAL_STATUSES:
                return result

            if time.monotonic() > deadline:
                raise TimeoutError(
                    f"Submission {submission_id} still '{state}' " f"after {timeout}s"
                )

            time.sleep(interval)

    # ---------------------------------------------------------- utilities

    def get_my_profile(self) -> dict[str, Any]:
        self._ensure_auth()

        resp = self.session.get(f"{self.host}/api/my_profile/")
        resp.raise_for_status()
        return resp.json()

    def list_queues(self, **params: Any) -> list[dict[str, Any]]:
        self._ensure_auth()

        resp = self.session.get(f"{self.host}/api/queues/", params=params)
        resp.raise_for_status()
        return resp.json()["results"]
