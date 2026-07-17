import pytest

from scenarios.common.config import Settings, _PROJECT_ROOT


def test_project_root_contains_env_example():
    assert (_PROJECT_ROOT / ".env.example").is_file(), (
        f"_PROJECT_ROOT ({_PROJECT_ROOT}) does not contain .env.example — "
        "the path calculation in config.py is broken"
    )


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
