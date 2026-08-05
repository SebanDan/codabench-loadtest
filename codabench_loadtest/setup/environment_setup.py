from pathlib import Path

from codabench_loadtest.clients import CodabenchClient
from codabench_loadtest.models import CompetitionPool, User, UserPool
from codabench_loadtest.setup import Settings


class EnvironmentSetup:
    """
    Class to set up the environment for load testing.
    """

    def __init__(self, settings: Settings):
        self.settings = settings
        self.codabench_client = CodabenchClient(config=settings)
        self.codabench_client.login()
        self.dataset_ids: list[int] = []

    def create_user_pools(self, size: int = 10) -> UserPool:
        """
        Create a pool of active users for load testing.

        Users are created through the Django admin, so they are active
        immediately and require no e-mail validation.
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
        """Register a pool of users to a competition."""
        for user in user_pool.users:
            self.codabench_client.register_to_competition(
                username=user.username,
                password=user.password,
                competition_id=competition_id,
            )

    def create_competition(self, bundle_path: Path):
        """Create a competition from a bundle and publish it."""
        result = self.codabench_client.create_competition(bundle_path)
        competition_id = result.get("resulting_competition")
        if competition_id is not None:
            self.codabench_client.publish_competition(competition_id)
        return result

    def get_competition_first_phase(self, competition_id: int) -> int:
        """Get the first phase ID of a competition."""
        competition_data = self.codabench_client.get_competition(competition_id)
        phases = competition_data["phases"]
        return phases[0].get("id") or competition_id

    def get_competition_pool(
        self, competition_dir: Path, competition_filter: list[str] | None = None
    ) -> CompetitionPool:
        """Get a pool of competitions from a directory."""
        return CompetitionPool.from_dir(
            competition_dir, competition_filter=competition_filter
        )

    def delete_users(self, user_pool: UserPool):
        """Delete all users in the provided user pool."""
        user_ids = [user.id for user in user_pool.users if user.id is not None]
        print(f"Deleting {len(user_ids)} users")
        self.codabench_client.delete_users(user_ids)

    def delete_competition(self, competition_id: int):
        """Delete a competition by its ID."""
        print(f"Deleting competition with ID: {competition_id}")
        self.codabench_client.delete_competition(competition_id)

    def delete_datasets(self):
        """Delete all datasets that were uploaded during the load test."""
        # TODO: Fix this method to delete only the datasets that were uploaded during the load test.
        # This currently throws an error from the API because the datasets does not belong to the admin user.
        # print(f"Deleting {len(self.dataset_ids)} datasets")
        # self.codabench_client.delete_datasets(dataset_ids=self.dataset_ids)
        self.codabench_client.delete_unused_datasets()
