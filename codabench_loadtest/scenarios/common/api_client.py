from __future__ import annotations

import time
from pathlib import Path
from typing import Any

import requests

from codabench_loadtest.scenarios.common.config import Settings
from codabench_loadtest.scenarios.utils import validate_competition_bundle

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

    def __init__(
        self, config: Settings, custom_session: requests.Session | None = None
    ) -> None:
        self.host = config.host.rstrip("/")
        self.session = custom_session or requests.Session()
        self._authenticated = False
        self.settings = config

    # ------------------------------------------------------------------ auth

    def login(self) -> None:
        self.settings.require_auth()

        token = self.settings.api_token.get_secret_value()
        if token:
            self.session.headers["Authorization"] = f"Token {token}"
            self._authenticated = True
            return

        resp = self.session.post(
            f"{self.host}/api/api-token-auth/",
            json={
                "username": self.settings.username,
                "password": self.settings.password.get_secret_value(),
            },
        )
        resp.raise_for_status()
        self.session.headers["Authorization"] = f"Token {resp.json()['token']}"
        self._authenticated = True

    def _ensure_auth(self) -> None:
        if not self._authenticated:
            self.login()

    def create_user(self, username: str, password: str) -> None:
        """Create an active Codabench user via the Django admin.

        Uses a dedicated session so the admin's session/CSRF cookies don't
        leak into the token-authenticated API session (which would make DRF
        enforce CSRF on subsequent API writes).
        """
        admin = requests.Session()

        # Log into the admin to get a session cookie (the DRF token doesn't
        # authenticate the admin site).
        login_url = f"{self.host}/admin/login/"
        admin.get(login_url)  # sets the csrftoken cookie
        admin.post(
            login_url,
            data={
                "username": self.settings.username,
                "password": self.settings.password.get_secret_value(),
                "csrfmiddlewaretoken": admin.cookies["csrftoken"],
                "next": "/admin/",
            },
            headers={"Referer": login_url},
        ).raise_for_status()

        add_url = f"{self.host}/admin/profiles/user/add/"
        admin.get(add_url)  # refresh the csrftoken cookie
        resp = admin.post(
            add_url,
            data={
                "username": username,
                "usable_password": "true",
                "password1": password,
                "password2": password,
                "csrfmiddlewaretoken": admin.cookies["csrftoken"],
                "_save": "Save",
            },
            headers={"Referer": add_url},
        )
        resp.raise_for_status()
        if "/change/" not in resp.url:
            raise RuntimeError(f"Failed to create user {username!r} via admin.")

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

    def create_competition(
        self,
        bundle_path: Path,
        *,
        interval: float | None = None,
        timeout: float | None = None,
    ) -> dict[str, Any]:
        self._ensure_auth()

        validate_competition_bundle(bundle_path)

        resp = self.session.post(
            f"{self.host}/api/datasets/",
            data={
                "type": "competition_bundle",
                "request_sassy_file_name": bundle_path.name,
                "file_name": bundle_path.name,
                "file_size": bundle_path.stat().st_size,
            },
        )
        resp.raise_for_status()
        upload = resp.json()

        with bundle_path.open("rb") as bundle_file:
            resp = self.session.put(
                upload["sassy_url"],
                data=bundle_file,
                headers={"Content-Type": "application/zip"},
                timeout=(10, 300),
            )
        resp.raise_for_status()

        resp = self.session.put(f"{self.host}/api/datasets/completed/{upload['key']}/")
        resp.raise_for_status()
        return self.poll_until_done(
            func=self.get_competition_creation_status,
            status_id=resp.json()["status_id"],
            interval=interval,
            timeout=timeout,
        )

    def delete_competition(self, competition_id: int) -> dict[str, Any]:
        self._ensure_auth()
        resp = self.session.delete(f"{self.host}/api/competitions/{competition_id}/")
        resp.raise_for_status()
        return {"status_code": resp.status_code}

    def get_competition_creation_status(self, status_id: int) -> dict[str, Any]:
        self._ensure_auth()
        resp = self.session.get(
            f"{self.host}/api/competitions/{status_id}/creation_status/"
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
        func,
        status_id: int,
        *,
        interval: float | None = None,
        timeout: float | None = None,
    ) -> dict[str, Any]:
        interval = interval or self.settings.poll_interval
        timeout = timeout or self.settings.poll_timeout
        deadline = time.monotonic() + timeout

        while True:
            result = func(status_id)
            state = result.get("status", "")

            if state in TERMINAL_STATUSES:
                return result

            if time.monotonic() > deadline:
                raise TimeoutError(
                    f"Status {status_id} still '{state}' " f"after {timeout}s"
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
