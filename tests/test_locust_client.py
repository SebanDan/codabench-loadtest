from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, Mock

import pytest
from requests.exceptions import HTTPError

from codabench_loadtest.clients.base_api_client import CodabenchClient
from codabench_loadtest.clients.exceptions import (
    DatasetCompletionError,
    DatasetCreateError,
    SubmissionCancellationError,
    SubmissionCreationError,
)
from codabench_loadtest.clients.locust_api_client import CodabenchLocustClient


def make_settings() -> Mock:
    return Mock(
        host="http://localhost:8000",
        caddy_hostname="localhost:80",
        minio_endpoint="http://localhost:9000",
    )


def make_response(
    *,
    status_code: int,
    json_data: dict | list | None = None,
    error: str = "boom",
    with_context: bool = False,
) -> MagicMock:
    response = MagicMock()
    response.status_code = status_code
    response.json.return_value = json_data
    response.error = error
    response.raise_for_status.return_value = None
    if with_context:
        response.__enter__.return_value = response
        response.__exit__.return_value = False
    return response


def make_client(client_cls, session: Mock) -> CodabenchClient:
    session.headers = {}
    if client_cls is CodabenchLocustClient:
        client = client_cls(config=make_settings(), session=session)
    else:
        client = client_cls(config=make_settings())
    client.session = session
    client._authenticated = True
    return client


def test_codabench_client_create_competition_raises_on_dataset_creation_error(
    tmp_path: Path,
    monkeypatch,
):
    bundle_path = tmp_path / "bundle.zip"
    bundle_path.write_bytes(b"bundle-bytes")

    session = Mock()
    response = make_response(status_code=500)
    response.raise_for_status.side_effect = HTTPError("500 Server Error")
    session.post.return_value = response

    client = make_client(CodabenchClient, session)

    monkeypatch.setattr(
        "codabench_loadtest.clients.base_api_client.Session",
        Mock(side_effect=AssertionError("upload should not be attempted")),
    )

    with pytest.raises(HTTPError, match="500 Server Error"):
        client.create_competition(bundle_path)

    session.post.assert_called_once()


def test_codabench_client_delete_datasets_raises_on_api_error():
    session = Mock()
    response = make_response(status_code=500)
    response.raise_for_status.side_effect = HTTPError("500 Server Error")
    session.post.return_value = response

    client = make_client(CodabenchClient, session)

    with pytest.raises(HTTPError, match="500 Server Error"):
        client.delete_datasets([1, 2, 3])

    session.post.assert_called_once_with(
        "http://localhost:8000/api/datasets/delete_many/",
        json=[1, 2, 3],
    )


def test_codabench_locust_client_upload_submission_marks_failed_on_dataset_create_error(
    monkeypatch,
):
    response = make_response(status_code=500, with_context=True)
    session = Mock()
    session.post.return_value = response

    client = make_client(CodabenchLocustClient, session)

    monkeypatch.setattr(
        "codabench_loadtest.clients.locust_api_client.Session",
        Mock(side_effect=AssertionError("binary upload should not be attempted")),
    )

    with pytest.raises(DatasetCreateError, match="Dataset creation failed"):
        client.upload_submission(
            competition_id=1,
            zip_bytes=b"zip-bytes",
            zip_name="submission.zip",
            size=123,
        )

    response.failure.assert_called_once_with("dataset create failed: 500 boom")


def test_codabench_locust_client_upload_submission_marks_failed_on_completion_error(
    monkeypatch,
):
    create_response = make_response(
        status_code=201,
        json_data={"key": "dataset-key", "sassy_url": "http://minio.local/upload"},
        with_context=True,
    )
    completion_response = make_response(status_code=500, with_context=True)
    session = Mock()
    session.post.return_value = create_response
    session.put.return_value = completion_response

    client = make_client(CodabenchLocustClient, session)

    binary_upload_response = make_response(status_code=200, with_context=True)
    binary_upload_session = Mock()
    binary_upload_session.put.return_value = binary_upload_response
    monkeypatch.setattr(
        "codabench_loadtest.clients.locust_api_client.Session",
        Mock(return_value=binary_upload_session),
    )

    with pytest.raises(DatasetCompletionError, match="Dataset completion failed"):
        client.upload_submission(
            competition_id=1,
            zip_bytes=b"zip-bytes",
            zip_name="submission.zip",
            size=123,
        )

    completion_response.failure.assert_called_once_with(
        "dataset completion failed: 500: boom"
    )


def test_codabench_locust_client_create_submission_marks_failed_on_error():
    response = make_response(status_code=500, with_context=True)
    session = Mock()
    session.post.return_value = response

    client = make_client(CodabenchLocustClient, session)

    with pytest.raises(SubmissionCreationError, match="Submission creation failed"):
        client.create_submission(key="dataset-key", phase=2, name="submission")

    response.failure.assert_called_once_with("submission failed: 500 boom")


def test_codabench_locust_client_cancel_submission_marks_failed_on_error():
    response = make_response(status_code=500)
    session = Mock()
    session.get.return_value = response

    client = make_client(CodabenchLocustClient, session)

    with pytest.raises(SubmissionCancellationError, match="Submission cancellation failed"):
        client.cancel_submission(submission_id=42)

    response.failure.assert_called_once_with("cancel submission failed: 500 boom")