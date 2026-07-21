from pathlib import Path

from locust import events

from codabench_loadtest.common import EnvironmentSetup, Settings
from codabench_loadtest.scenarios.users import SmokeUser, SubmitterUser

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"
SUBMISSION_DIR = DATA_DIR / "submissions"
ENV_DIR = ROOT_DIR / ".github" / "env"


@events.init_command_line_parser.add_listener
def _(parser):
    parser.add_argument(
        "--env",
        type=str,
        default="local",
        choices=["local", "prod"],
        help="Environnement cible (surcharge CODABENCH_ENV si fourni)",
    )


@events.init.add_listener
def on_init(environment, **kwargs):
    env_file = ENV_DIR / f"{environment.parsed_options.env}.env"
    codabench_settings = Settings(_env_file=env_file)  # type: ignore[call-arg]
    environment.codabench_settings = codabench_settings

    env_setup = EnvironmentSetup(codabench_settings)
    environment.env_setup = env_setup
    environment.data_dir = DATA_DIR
    environment.submission_dir = SUBMISSION_DIR
    environment.submission_pool = env_setup.get_submission_pool(SUBMISSION_DIR)


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    result = environment.env_setup.create_competition(
        bundle_path=DATA_DIR / environment.codabench_settings.competition_bundle
    )
    environment.competition_id = result.get("resulting_competition")
    user_pool = environment.env_setup.create_user_pools(
        size=environment.parsed_options.num_users
    )
    environment.user_pool = user_pool


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    environment.env_setup.delete_users(environment.user_pool)
    environment.env_setup.delete_competition(environment.competition_id)
