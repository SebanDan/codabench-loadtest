from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType
from unittest.mock import Mock

import pytest

from codabench_loadtest.clients.exceptions import LoadTestError


def load_submitter_user_class(monkeypatch) -> type:
    locust_stub = ModuleType("locust")

    class HttpUser:
        pass

    def passthrough_decorator(*decorator_args, **decorator_kwargs):
        if (
            len(decorator_args) == 1
            and callable(decorator_args[0])
            and not decorator_kwargs
        ):
            return decorator_args[0]

        def decorator(func):
            return func

        return decorator

    locust_stub.HttpUser = HttpUser
    locust_stub.between = lambda *args, **kwargs: lambda: None
    locust_stub.tag = passthrough_decorator
    locust_stub.task = passthrough_decorator
    monkeypatch.setitem(sys.modules, "locust", locust_stub)

    module_path = (
        Path(__file__).resolve().parents[1]
        / "codabench_loadtest"
        / "scenarios"
        / "users"
        / "submitter_user.py"
    )
    spec = importlib.util.spec_from_file_location(
        "submitter_user_under_test", module_path
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module.SubmitterUser


def make_submitter_user(monkeypatch) -> object:
    submitter_user_class = load_submitter_user_class(monkeypatch)
    user = submitter_user_class.__new__(submitter_user_class)
    user.environment = Mock()
    user.environment.events.request = Mock()
    user.codabench_client = Mock()
    return user


def make_competition() -> Mock:
    competition = Mock()
    competition.name = "IRIS"
    competition.id = 12
    competition.get_phase_id.return_value = 34
    return competition


def make_submission_zip() -> Mock:
    submission_zip = Mock()
    submission_zip.zip_name = "submission.zip"
    submission_zip.get_zip_bytes.return_value = b"zip-bytes"
    submission_zip.bytes_size.return_value = 123
    return submission_zip


def test_submitter_user_submit_records_locust_failure_when_submission_is_failed(
    monkeypatch,
):
    user = make_submitter_user(monkeypatch)
    competition = make_competition()
    submission_zip = make_submission_zip()

    user.codabench_client.upload_submission.return_value = {"key": "dataset-key"}
    user.codabench_client.create_submission.return_value = {"id": 99}
    user.codabench_client.poll_until_done.return_value = None
    user.codabench_client.get_submission.return_value = {
        "status": "Failed",
        "message": "model execution failed",
    }

    with pytest.raises(LoadTestError, match="Submission 99 failed"):
        user._submit(competition=competition, submission_zip=submission_zip)

    user.environment.events.request.fire.assert_called_once()
    fire_call = user.environment.events.request.fire.call_args.kwargs
    assert fire_call["request_type"] == "submission"
    assert fire_call["name"] == "IRIS submission.zip"
    assert fire_call["response_time"] == 0
    assert fire_call["response_length"] == 0
    assert isinstance(fire_call["exception"], LoadTestError)

    user.codabench_client.upload_submission.assert_called_once_with(
        12,
        zip_bytes=b"zip-bytes",
        zip_name="submission.zip",
        size=123,
        custom_name="IRIS submission.zip",
    )
    user.codabench_client.create_submission.assert_called_once_with(
        "dataset-key",
        phase=34,
        name="IRIS submission.zip",
    )