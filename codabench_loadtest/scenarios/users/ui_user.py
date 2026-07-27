import re
from typing import TYPE_CHECKING

from locust import between, tag, task
from locust_plugins.users.playwright import (  # type: ignore
    PageWithRetry,
    PlaywrightUser,
    event,
    pw,
)
from playwright.async_api import expect  # type: ignore

from codabench_loadtest.models import User
from codabench_loadtest.scenarios.tasks.playwright import login

if TYPE_CHECKING:
    from codabench_loadtest.models import SubmissionZip


class UIUser(PlaywrightUser):
    """A user that performs various tasks on the codabench platform through the UI."""

    wait_time = between(1, 2)

    async def _ensure_auth(self, page: PageWithRetry) -> User:
        codabench_user: User = self.environment.user_pool.get_random_user()
        async with event(self, "[UI] Login"):
            await login(
                page,
                codabench_user.username,
                codabench_user.password,
            )
        return codabench_user

    @tag("health")  # type: ignore
    @task  # type: ignore
    @pw
    async def check_submit_button(self, page: PageWithRetry):
        await self._ensure_auth(page)

        async with event(self, "[UI] Check competition page"):
            await page.goto(f"/competitions/{self.environment.competition_id}/")
        await page.click('button:has-text("Submit")')

    @tag("normal")  # type: ignore
    @task  # type: ignore
    @pw
    async def submit_task(self, page: PageWithRetry):
        user = await self._ensure_auth(page)
        submission: SubmissionZip = (
            self.environment.submission_pool.get_random_submission_zip()
        )
        async with event(self, f"[UI] Submit task {submission.zip_name}"):
            await page.get_by_text("My Submissions").click()

            async with page.expect_file_chooser() as fc_info:
                await page.get_by_role("button", name=" ").click()
            file_chooser = await fc_info.value
            await file_chooser.set_files(str(submission.zip_path))

            await expect(page.locator(".ui.indicating")).to_be_visible()
            await expect(page.locator(".ui.indicating")).not_to_be_visible()

            finished_or_failed = re.compile(r"^(Finished|Failed.*)$")
            try:
                await expect(
                    page.get_by_role("cell", name=finished_or_failed)
                ).to_be_visible(timeout=25000)
            except Exception:
                await page.reload()
                await expect(
                    page.get_by_role("cell", name=finished_or_failed)
                ).to_be_visible(timeout=2000)

            try:
                await expect(page.get_by_role("cell", name="Finished")).to_be_visible()

                text = await page.locator(".submission_row").first.inner_text()
                submission_id = text.split(None, 1)

                try:
                    await page.locator("td:nth-child(6) > span > .icon").first.click(
                        timeout=300
                    )
                except Exception:
                    await page.locator("td:nth-child(7) > span > .icon").first.click(
                        timeout=300
                    )

                await page.locator("div").filter(
                    has_text=re.compile(r"^Results$")
                ).click()
                await expect(
                    page.locator("#leaderboardTable").get_by_role(
                        "link", name=user.username
                    )
                ).to_be_visible()
                await expect(
                    page.get_by_role("cell", name=submission_id[0], exact=True)
                ).to_be_visible()

            except Exception as e:
                raise ValueError(
                    f"Unexpected submission status for submission_id={submission_id[0]!r}. "
                    f"Expected 'Finished'. {e}"
                ) from e
