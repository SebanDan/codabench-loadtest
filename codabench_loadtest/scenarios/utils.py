from __future__ import annotations

import zipfile
from pathlib import Path
from typing import TYPE_CHECKING, Any, BinaryIO

if TYPE_CHECKING:
    from locust.clients import HttpSession


def authenticate(client: HttpSession, username: str, password: str):
    response = client.post(
        "/api/api-token-auth/", json={"username": username, "password": password}
    )
    response.raise_for_status()
    client.headers.update({"Authorization": f"Token {response.json()['token']}"})


def upload_submission(
    client: HttpSession,
    competition_id: int,
    zip_bytes: bytes | BinaryIO,
    zip_name: str,
    size: int,
) -> Any:
    with client.post(
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
    with client.put(
        sassy_url,
        data=zip_bytes,
        headers={"Authorization": None, "Content-Type": "application/zip"},
        name="PUT [storage upload]",
        catch_response=True,
    ) as response:
        if response.status_code not in (200, 201, 204):
            response.failure(f"storage upload failed: {response.status_code}")
            return

    with client.put(
        f"/api/datasets/completed/{key}/",
        name="/api/datasets/completed/[key]/",
        catch_response=True,
    ) as response:
        if response.status_code not in (200, 201, 204):
            response.failure(f"dataset completion failed: {response.status_code}")
            return
    return data


def create_submission(client: HttpSession, key: str, phase: int, name: str) -> Any:
    with client.post(
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


def validate_competition_bundle(bundle_path: Path):
    if not bundle_path.is_file():
        raise FileNotFoundError(f"Competition bundle not found: {bundle_path}")
    if bundle_path.suffix.lower() != ".zip":
        raise ValueError(f"Competition bundle must be a ZIP file: {bundle_path}")
    try:
        with zipfile.ZipFile(bundle_path) as bundle:
            if "competition.yaml" not in bundle.namelist():
                raise ValueError(
                    "Competition bundle must contain competition.yaml at its root"
                )
            bad_file = bundle.testzip()
            if bad_file is not None:
                raise ValueError(
                    f"Competition bundle contains a corrupt file: {bad_file}"
                )
    except zipfile.BadZipFile as error:
        raise ValueError(f"Invalid competition ZIP: {bundle_path}") from error


def cancel_submission(client: HttpSession, submission_id: int) -> Any:
    with client.get(
        f"/api/submissions/{submission_id}/cancel_submission/",
        name="/api/submissions/[id]/cancel_submission/",
        catch_response=True,
    ) as response:
        if response.status_code != 200:
            response.failure(
                f"cancel failed: {response.status_code} {response.text[:200]}"
            )
    return response.json()


def re_run_submission(client: HttpSession, submission_id: int) -> Any:
    with client.post(
        f"/api/submissions/{submission_id}/re_run_submission/",
        name=f"/api/submissions/{submission_id}/re_run_submission/",
        catch_response=True,
    ) as response:
        if response.status_code not in (200, 201):
            response.failure(
                f"re_run failed: {response.status_code} {response.text[:200]}"
            )
    return response.json()
