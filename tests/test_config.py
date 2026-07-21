import pytest

from codabench_loadtest.common.config import Settings

def test_poll_timeout_must_exceed_interval():
    with pytest.raises(ValueError, match="poll_timeout"):
        Settings(
            _env_file=None,  # type: ignore[call-arg]
            poll_interval=10.0,
            poll_timeout=5.0,
        )


def test_poll_timeout_equal_to_interval_rejected():
    with pytest.raises(ValueError, match="poll_timeout"):
        Settings(
            _env_file=None,  # type: ignore[call-arg]
            poll_interval=5.0,
            poll_timeout=5.0,
        )


def test_require_auth_raises_when_no_credentials():
    s = Settings(_env_file=None)  # type: ignore[call-arg]
    with pytest.raises(RuntimeError, match="Missing CODABENCH_API_TOKEN"):
        s.require_auth()


def test_require_auth_passes_with_token():
    from pydantic import SecretStr

    s = Settings(_env_file=None, api_token=SecretStr("tok123"))  # type: ignore[call-arg]
    s.require_auth()


def test_require_auth_passes_with_username():
    s = Settings(_env_file=None, username="user1")  # type: ignore[call-arg]
    s.require_auth()
