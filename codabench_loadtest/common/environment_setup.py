from pathlib import Path

from codabench_loadtest.common import CodabenchClient, Settings
from codabench_loadtest.models import SubmissionPool, User, UserPool


class EnvironmentSetup:
    """
    Class to set up the environment for load testing.
    """

    def __init__(self, settings: Settings):
        self.settings = settings
        self.codabench_client = CodabenchClient(config=settings)
        self.codabench_client.login()

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
            details = self.codabench_client.create_user(
                username=user.username, password=user.password, email=user.email
            )
            user.id = details["id"]
            pool.users.append(user)
        return pool

    def create_competition(self, bundle_path: Path):
        return self.codabench_client.create_competition(bundle_path)

    def get_submission_pool(self, submission_dir: Path):
        return SubmissionPool.from_dir(submission_dir)

    def delete_users(self, user_pool: UserPool):
        for user in user_pool.users:
            if user.id is not None:
                self.codabench_client.delete_user(user.id)

    def delete_competition(self, competition_id: int):
        self.codabench_client.delete_competition(competition_id)
