import pytest
from pydantic import SecretStr

from codabench_loadtest.setup.config import Settings


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


@pytest.mark.parametrize(
    "token,username,password",
    [
        (SecretStr("tok123"), "", SecretStr("")),
        (SecretStr(""), "user1", SecretStr("pass2")),
    ],
)
def test_require_auth_passes(token, username, password):
    s = Settings(_env_file=None, api_token=token, username=username, password=password)  # type: ignore[call-arg]
    s.require_auth()


@pytest.mark.parametrize(
    "token,username,password",
    [
        (SecretStr(""), "", SecretStr("")),
        (SecretStr(""), "user1", SecretStr("")),
        (SecretStr(""), "", SecretStr("pass2")),
    ],
)
def test_require_auth_raise(token, username, password):
    s = Settings(_env_file=None, api_token=token, username=username, password=password)  # type: ignore[call-arg]
    with pytest.raises(
        RuntimeError,
        match="Missing CODABENCH_API_TOKEN or CODABENCH_USERNAME/PASSWORD in .env",
    ):
        s.require_auth()
