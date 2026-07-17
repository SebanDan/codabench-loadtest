from pathlib import Path

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

_PROJECT_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=_PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        env_prefix="CODABENCH_",
        extra="ignore",
    )

    # Target host
    host: str = "http://localhost:8000"

    # Authentication
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


settings = Settings()
