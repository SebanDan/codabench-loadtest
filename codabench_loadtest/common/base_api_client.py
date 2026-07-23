from __future__ import annotations

import time
from collections.abc import Iterable
from pathlib import Path
from typing import Any

import requests

from codabench_loadtest.common.config import Settings
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
    """A basic client for the Codabench REST API."""

    def __init__(self, config: Settings) -> None:
        self.host = config.host.rstrip("/")
        self.settings = config
        self.session = requests.Session()
        self._authenticated = False

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
        self.session.headers.update({"Authorization": f"Token {resp.json()['token']}"})
        self._authenticated = True

    def _ensure_auth(self) -> None:
        if not self._authenticated:
            self.login()

    def create_user(self, username: str, password: str, email: str) -> dict[str, Any]:
        """Create an active Codabench user via the Django admin.

        Uses a dedicated session so the admin's session/CSRF cookies don't
        leak into the token-authenticated API session (which would make DRF
        enforce CSRF on subsequent API writes).
        """
        admin = requests.Session()

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

        user_id = str(resp.url.rstrip("/").split("/")[-2])

        self.patch_user(user_id=user_id, json_data={"email": email})
        return {"id": user_id}

    def patch_user(self, user_id: str, json_data: dict) -> dict[str, Any]:
        self._ensure_auth()
        response = self.session.patch(
            f"{self.host}/api/users/{user_id}/",
            json=json_data,
        )
        response.raise_for_status()
        return response.json()

    def delete_users(self, user_ids: list[str]) -> None:
        """Hard-delete users via the Django admin bulk action.

        ``User.delete()`` is overridden to only *soft* delete (anonymize and
        rename to ``deleted_user_<id>``). The admin changelist
        ``delete_selected`` action calls ``QuerySet.delete()`` instead, which
        bypasses that override and removes the rows for real. Doing it in a
        single request also avoids one round-trip per user.
        """
        if not user_ids:
            return

        admin = requests.Session()

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

        changelist_url = f"{self.host}/admin/profiles/user/"
        admin.get(changelist_url)  # refresh the csrftoken cookie
        resp = admin.post(
            changelist_url,
            data={
                "action": "delete_selected",
                "post": "yes",
                "select_across": "0",
                "index": "0",
                "_selected_action": [str(uid) for uid in user_ids],
                "csrfmiddlewaretoken": admin.cookies["csrftoken"],
            },
            headers={"Referer": changelist_url},
        )
        resp.raise_for_status()

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

    def get_competition(self, competition_id: int):
        self._ensure_auth()
        response = self.session.get(f"{self.host}/api/competitions/{competition_id}/")
        response.raise_for_status()
        return response.json()

    def publish_competition(self, competition_id: int) -> dict[str, Any]:
        """Publish a competition and auto-approve its participants."""
        self._ensure_auth()
        resp = self.session.patch(
            f"{self.host}/api/competitions/{competition_id}/",
            json={
                "published": True,
                "registration_auto_approve": True,
                "whitelist_emails": [],
            },
        )
        resp.raise_for_status()
        return resp.json()

    def register_to_competition(
        self, username: str, password: str, competition_id: int
    ) -> dict[str, Any]:
        """Register a user as a participant of the competition."""
        session = requests.Session()
        resp = session.post(
            f"{self.host}/api/api-token-auth/",
            json={"username": username, "password": password},
        )
        resp.raise_for_status()
        token = resp.json()["token"]
        resp = session.post(
            f"{self.host}/api/competitions/{competition_id}/register/",
            headers={"Authorization": f"Token {token}"},
        )
        resp.raise_for_status()
        return resp.json()

    def list_submissions(self, competition_id: int) -> list[dict[str, Any]]:
        """List all (non-soft-deleted) submissions of a competition.

        Uses ``page_size=all`` to fetch every submission in a single call
        (capped server-side at 1000).
        """
        self._ensure_auth()
        params: dict[str, str] = {
            "phase__competition": str(competition_id),
            "page_size": "all",
        }
        resp = self.session.get(f"{self.host}/api/submissions/", params=params)
        resp.raise_for_status()
        payload = resp.json()
        if isinstance(payload, dict):
            return payload.get("results", [])
        return payload

    def wait_for_submissions_completed(
        self,
        competition_id: int,
        *,
        interval: float | None = None,
        timeout: float | None = None,
    ) -> None:
        """Block until every submission of the competition is terminal."""
        for submission in self.list_submissions(competition_id):
            if submission.get("status") in TERMINAL_STATUSES:
                continue
            self.poll_until_done(
                self.get_submission,
                submission["id"],
                interval=interval,
                timeout=timeout,
            )

    def delete_competition(
        self,
        competition_id: int,
    ) -> dict[str, Any]:
        """Delete a competition after draining its in-flight submissions."""
        self._ensure_auth()
        self.wait_for_submissions_completed(competition_id)
        resp = self.session.delete(f"{self.host}/api/competitions/{competition_id}/")
        resp.raise_for_status()
        return {"status_code": resp.status_code}

    def list_dataset_ids(self, *, kind: str) -> set[int]:
        """Return the ids of the authenticated user's datasets of ``kind``.

        ``kind`` maps to the API ``_type`` filter: ``"dataset"`` (input,
        reference, scoring, ingestion, starting kit, solution), ``"bundle"``
        (competition bundle) or ``"submission"``. The endpoint only returns
        datasets owned by the caller, so this is scoped to the admin account.
        """
        self._ensure_auth()
        ids: set[int] = set()
        page = 1
        while True:
            resp = self.session.get(
                f"{self.host}/api/datasets/",
                params={"_type": kind, "page_size": "1000", "page": str(page)},
            )
            resp.raise_for_status()
            payload = resp.json()
            results = (
                payload.get("results", []) if isinstance(payload, dict) else payload
            )
            ids.update(item["id"] for item in results)
            if not (isinstance(payload, dict) and payload.get("next")):
                break
            page += 1
        return ids

    def delete_datasets(self, dataset_ids: Iterable[int]) -> None:
        """Bulk-delete datasets owned by the authenticated user."""
        ids = list(dataset_ids)
        if not ids:
            return
        self._ensure_auth()
        resp = self.session.post(
            f"{self.host}/api/datasets/delete_many/",
            json=ids,
        )
        resp.raise_for_status()

    def get_competition_creation_status(self, status_id: int) -> dict[str, Any]:
        self._ensure_auth()
        resp = self.session.get(
            f"{self.host}/api/competitions/{status_id}/creation_status/"
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
