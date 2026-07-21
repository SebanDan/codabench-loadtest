from pathlib import Path

from locust import events

from codabench_loadtest.common import EnvironmentSetup, Settings
from codabench_loadtest.scenarios.users import SmokeUser

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"
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
    result = env_setup.create_competition(
        bundle_path=DATA_DIR / codabench_settings.competition_bundle
    )
    user_pool = env_setup.create_user_pools(size=2)
    environment.competition_id = result.get("resulting_competition")
    environment.user_pool = user_pool
    environment.data_dir = DATA_DIR
    environment.setup = env_setup


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    pass


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    environment.setup.delete_users(environment.user_pool)
    environment.setup.delete_competition(environment.competition_id)
