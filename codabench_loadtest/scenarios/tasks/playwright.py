from __future__ import annotations

from typing import TYPE_CHECKING

from locust_plugins.users.playwright import PageWithRetry, PlaywrightUser

if TYPE_CHECKING:
    from codabench_loadtest.setup.config import Settings


class PlaywrightBaseUser(PlaywrightUser):
    """A base user class that provides common functionality for all user types."""

    abstract = True
    codabench_settings: Settings
    host: str | None = None

    def on_start(self):
        self.codabench_settings: Settings = self.environment.codabench_settings
        self.host = self.codabench_settings.host

    async def login(self, page: PageWithRetry, username: str, password: str) -> None:
        await page.goto("/")
        await page.get_by_role("link", name="Login").click()
        await page.get_by_role("textbox", name="username or email").click()
        await page.get_by_role("textbox", name="username or email").fill(username)
        await page.get_by_role("textbox", name="password").click()
        await page.get_by_role("textbox", name="password").fill(password)
        await page.get_by_role("button", name="Log In").click()
