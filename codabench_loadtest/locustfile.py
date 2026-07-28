from pathlib import Path

from locust import events

from codabench_loadtest.scenarios.users import SmokeUser, SubmitterUser, UIUser
from codabench_loadtest.setup import EnvironmentSetup, Settings

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"
SUBMISSION_DIR = DATA_DIR / "submissions"
ENV_DIR = ROOT_DIR / ".github" / "env"


@events.init_command_line_parser.add_listener
def _(parser):
    """Add custom command line arguments to the Locust parser."""
    parser.add_argument(
        "--env",
        type=str,
        default="local",
        choices=["local", "prod"],
        help="Environment file name to use for the load test (local or prod).",
    )
    parser.add_argument(
        "--competitions",
        type=str,
        nargs="+",
        default=None,
        help="List of competition names to filter the competitions to be tested.",
    )


@events.init.add_listener
def on_init(environment, **kwargs):
    """Initialize the environment with the required variables and settings."""
    env_file = ENV_DIR / f"{environment.parsed_options.env}.env"
    codabench_settings = Settings(_env_file=env_file)  # type: ignore[call-arg]
    environment.codabench_settings = codabench_settings

    env_setup = EnvironmentSetup(codabench_settings)
    environment.env_setup = env_setup
    environment.data_dir = DATA_DIR
    environment.competition_pool = env_setup.get_competition_pool(
        competition_dir=DATA_DIR,
        competition_filter=environment.parsed_options.competitions,
    )


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Handle actions to perform at the start of the test.
    This includes filtering user classes based on selected tasks, creating a competition, registering users.
    """

    # On test start, filter the users based on the selected tasks (filtered on tags) from the configuration file.
    environment.user_classes = [uc for uc in environment.user_classes if uc.tasks]
    user_pool = environment.env_setup.create_user_pools(
        size=environment.parsed_options.num_users
    )
    environment.user_pool = user_pool

    for competition in environment.competition_pool.competitions:

        result = environment.env_setup.create_competition(
            bundle_path=competition.bundle_path
        )
        competition.id = result.get("resulting_competition")
        competition.phase_id = environment.env_setup.get_competition_first_phase(
            competition_id=competition.id
        )
        environment.env_setup.register_user_pool(
            competition_id=competition.id, user_pool=user_pool
        )

    environment.env_setup.dataset_ids.extend(
        environment.env_setup.codabench_client.list_dataset_ids(
            kind="competition_bundle"
        )
    )


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Handle actions to perform at the end of the test.
    This includes deleting the competition and the user pool created for the test.
    """
    # Delete the competition first: its CASCADE FKs remove the participants and
    # submissions that reference the users.
    for competition in environment.competition_pool.competitions:
        environment.env_setup.delete_competition(competition.id)
    environment.env_setup.delete_users(environment.user_pool)
    environment.env_setup.delete_datasets()
