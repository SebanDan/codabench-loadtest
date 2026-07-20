from pathlib import Path

from dotenv import dotenv_values


class EnvironmentSetup:
    """
    Class to set up the environment for load testing.
    """

    def __init__(self, env_file: Path):
        self.env = {k: v for k, v in dotenv_values(env_file).items() if v is not None}

    def create_user_pool(
        self,
    ): ...

    def create_competition(
        self,
    ): ...

    def create_phase(self, competition_id: str): ...
