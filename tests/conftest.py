from pathlib import Path

from pydantic import SecretStr
from pytest import fixture

from codabench_loadtest.clients import CodabenchClient
from codabench_loadtest.setup.config import Settings

DATA_DIR = Path(__file__).resolve().parent / "data"
IRIS = DATA_DIR / "IRIS"


@fixture
def config():
    return Settings(
        host="http://localhost:8888",
        caddy_hostname="",
        api_token=SecretStr("tok123"),
        rabbitmq_url="http://localhost:17777",
        rabbitmq_user="mock_guest",
        rabbitmq_password=SecretStr("rabbit_password"),
    )


@fixture
def codabench_client(request):
    cfg = request.getfixturevalue("config")
    client = CodabenchClient(cfg)
    return client


@fixture
def competition_missing_competition_zip(tmp_path):
    # Create a temporary competition directory without a competition zip file
    competition_dir = tmp_path / "competition"
    competition_dir.mkdir()
    submissions_dir = competition_dir / "submissions"
    submissions_dir.mkdir()
    (submissions_dir / "submission1.zip").write_bytes(b"Submission content")
    return competition_dir


@fixture
def competition_multiple_zips(tmp_path):
    # Create a temporary competition directory with multiple zip files
    competition_dir = tmp_path / "competition"
    competition_dir.mkdir()
    (competition_dir / "competition1.zip").write_bytes(b"Zip content")
    (competition_dir / "competition2.zip").write_bytes(b"Zip content")
    submissions_dir = competition_dir / "submissions"
    submissions_dir.mkdir()
    (submissions_dir / "submission1.zip").write_bytes(b"Submission content")
    return competition_dir


@fixture
def competition_missing_submissions_dir(tmp_path):
    # Create a temporary competition directory without a submissions folder
    competition_dir = tmp_path / "competition"
    competition_dir.mkdir()
    (competition_dir / "competition.zip").write_bytes(b"Zip content")
    return competition_dir


@fixture
def competition_with_invalid_zip(tmp_path):
    # Create a temporary competition directory with an invalid zip file
    competition_dir = tmp_path / "competition"
    competition_dir.mkdir()
    (competition_dir / "competition.zip").write_bytes(b"Not a valid zip content")
    submissions_dir = competition_dir / "submissions"
    submissions_dir.mkdir()
    (submissions_dir / "submission1.zip").write_bytes(b"Submission content")
    (submissions_dir / "submission2.zip").write_bytes(b"Submission content")
    return competition_dir
