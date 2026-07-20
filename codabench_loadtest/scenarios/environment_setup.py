from pathlib import Path

from codabench_loadtest.scenarios.common import CodabenchClient, Settings
from codabench_loadtest.scenarios.models import User, UserPool


class EnvironmentSetup:
    """
    Class to set up the environment for load testing.
    """

    def __init__(self, settings: Settings):
        self.settings = settings
        self.codabench_client = CodabenchClient(config=settings)
        self.codabench_client.login()
        self.competition_id: int | None = None
        self.user_pool: UserPool | None = None

    def create_user_pools(self, size: int = 10) -> UserPool:
        """
        Create a pool of active users for load testing.

        Users are created through the Django admin, so they are active
        immediately and require no e-mail validation. Locust users can then
        pick a random user from the returned pool.
        """
        pool = UserPool()
        for _ in range(size):
            user = User()
            self.codabench_client.create_user(user.username, user.password)
            pool.users.append(user)
        self.user_pool = pool
        return pool

    def create_competition(self, bundle_path: Path):
        result = self.codabench_client.create_competition(bundle_path)
        self.competition_id = result.get("resulting_competition")
        return result
