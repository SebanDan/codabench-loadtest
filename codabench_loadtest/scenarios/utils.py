from __future__ import annotations

import zipfile
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from locust.clients import HttpSession


def authenticate(client: HttpSession, username: str, password: str):
    response = client.post(
        "/api/api-token-auth/", json={"username": username, "password": password}
    )
    response.raise_for_status()
    client.headers.update({"Authorization": f"Token {response.json()['token']}"})


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
