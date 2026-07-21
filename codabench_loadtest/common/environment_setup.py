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

    def register_user_pool(self, competition_id: int, user_pool: UserPool):
        for user in user_pool.users:
            self.codabench_client.register_to_competition(
                username=user.username,
                password=user.password,
                competition_id=competition_id,
            )

    def create_competition(self, bundle_path: Path):
        result = self.codabench_client.create_competition(bundle_path)
        competition_id = result.get("resulting_competition")
        if competition_id is not None:
            self.codabench_client.publish_competition(competition_id)
        return result

    def get_competition_first_phase(self, competition_id: int) -> int:
        competition_data = self.codabench_client.get_competition(competition_id)
        phases = competition_data["phases"]
        return phases[0].get("id") or competition_id

    def get_submission_pool(self, submission_dir: Path):
        return SubmissionPool.from_dir(submission_dir)

    def delete_users(self, user_pool: UserPool):
        user_ids = [user.id for user in user_pool.users if user.id is not None]
        self.codabench_client.delete_users(user_ids)

    def delete_competition(self, competition_id: int):
        self.codabench_client.delete_competition(competition_id)
