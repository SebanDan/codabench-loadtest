from pathlib import Path

from pydantic import SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_PROJECT_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    # All env vars use the CODABENCH_ prefix (e.g. CODABENCH_HOST,
    # CODABENCH_MINIO_ENDPOINT, CODABENCH_RABBITMQ_URL).
    model_config = SettingsConfigDict(
        env_file=_PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        env_prefix="CODABENCH_",
        extra="ignore",
    )

    # Target host
    host: str = "http://localhost:8000"

    # Authentication — defaults empty so anonymous web/ scenarios work.
    # Scenarios requiring auth must call require_auth() before use.
    username: str = ""
    password: SecretStr = SecretStr("")
    api_token: SecretStr = SecretStr("")

    # Polling behavior (seconds)
    poll_interval: float = 5.0
    poll_timeout: float = 3600.0

    # Submission defaults
    competition_id: int | None = None

    # Thresholds for assertions / reports
    max_response_time_p95: float = 2.0
    max_error_rate: float = 0.01

    # MinIO (for direct storage checks if needed)
    minio_endpoint: str = "http://localhost:9000"
    minio_access_key: str = ""
    minio_secret_key: SecretStr = SecretStr("")

    # RabbitMQ (for queue depth monitoring if needed)
    rabbitmq_url: str = "http://localhost:15672"
    rabbitmq_user: str = "guest"
    rabbitmq_password: SecretStr = SecretStr("")

    @model_validator(mode="after")
    def _check_poll_timeout_gt_interval(self) -> "Settings":
        if self.poll_timeout <= self.poll_interval:
            raise ValueError(
                f"poll_timeout ({self.poll_timeout}s) must be strictly greater "
                f"than poll_interval ({self.poll_interval}s)"
            )
        return self

    def require_auth(self) -> None:
        if not self.api_token.get_secret_value() and not self.username:
            raise RuntimeError(
                "Missing CODABENCH_API_TOKEN or CODABENCH_USERNAME/PASSWORD in .env"
            )


settings = Settings()
