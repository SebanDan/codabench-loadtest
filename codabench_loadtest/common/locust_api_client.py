from __future__ import annotations

from typing import TYPE_CHECKING, Any, BinaryIO, Mapping

from codabench_loadtest.common.base_api_client import CodabenchClient

if TYPE_CHECKING:
    from locust.clients import HttpSession

    from codabench_loadtest.common.config import Settings


def get_custom_codabench_locust_client(
    client: HttpSession, settings: Settings, update: Mapping[str, Any] | None = None
) -> CodabenchLocustClient:
    custom_settings = settings.model_copy(update=update)
    return CodabenchLocustClient(config=custom_settings, session=client)


class CodabenchLocustClient(CodabenchClient):
    """Reusable client for the Codabench REST API dedicated to Locust load testing."""

    def __init__(
        self,
        config: Settings,
        session: HttpSession,
    ) -> None:
        super().__init__(config=config)
        self.session = session

    def upload_submission(
        self,
        competition_id: int,
        zip_bytes: bytes | BinaryIO,
        zip_name: str,
        size: int,
    ) -> Any:

        with self.session.post(
            "/api/datasets/",
            json={
                "type": "submission",
                "competition": competition_id,
                "request_sassy_file_name": zip_name,
                "file_name": zip_name,
                "file_size": size,
            },
            name=f"/api/datasets/ [create submission {zip_name}]",
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
        with self.session.put(
            sassy_url,
            data=zip_bytes,
            headers={"Authorization": None, "Content-Type": "application/zip"},
            name="PUT [storage upload]",
            catch_response=True,
        ) as response:
            if response.status_code not in (200, 201, 204):
                response.failure(f"storage upload failed: {response.status_code}")
                return

        with self.session.put(
            f"/api/datasets/completed/{key}/",
            name="/api/datasets/completed/[key]/",
            catch_response=True,
        ) as response:
            if response.status_code not in (200, 201, 204):
                response.failure(f"dataset completion failed: {response.status_code}")
                return
        return data

    def create_submission(self, key: str, phase: int, name: str) -> Any:
        with self.session.post(
            "/api/submissions/",
            json={
                "data": key,
                "phase": phase,
                "tasks": [],
                "organization": None,
            },
            name=f"/api/submissions/ [create {name}]",
            catch_response=True,
        ) as response:
            if response.status_code not in (200, 201):
                response.failure(
                    f"submission failed: {response.status_code} {response.text[:200]}"
                )
                return
        return response.json()

    def cancel_submission(self, submission_id: int) -> Any:
        response = self.session.get(
            f"/api/submissions/{submission_id}/cancel_submission/",
            name="/api/submissions/[id]/cancel_submission/",
            catch_response=True,
        )
        response.raise_for_status()
        return response.json()
