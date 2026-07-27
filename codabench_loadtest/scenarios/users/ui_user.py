import re

from locust import between, tag, task
from locust_plugins.users.playwright import PageWithRetry, PlaywrightUser, event, pw
from playwright.sync_api import expect

from codabench_loadtest.models import User
from codabench_loadtest.scenarios.tasks.playwright import login


class UIUser(PlaywrightUser):
    """A user that performs various tasks on the codabench platform through the UI."""

    wait_time = between(1, 2)

    def on_start(self):
        self.codabench_user: User = self.environment.user_pool.get_random_user()
        self._logged_in = False

    async def _ensure_auth(self, page: PageWithRetry):
        if not self._logged_in:
            async with event(self, "[UI] Login"):
                await login(
                    page,
                    self.codabench_user.username,
                    self.codabench_user.password,
                )
            self._logged_in = True

    @tag("health")
    @task
    @pw
    async def check_submit_button(self, page: PageWithRetry):
        await self._ensure_auth(page)

        async with event(self, "[UI] Load competition page"):
            await page.goto(f"/competitions/{self.environment.competition_id}/")
        await page.click('button:has-text("Submit")')

    @tag("normal")
    @task
    @pw
    async def submit_task(self, page: PageWithRetry):
        await self._ensure_auth(page)
        submission = self.environment.submission_pool.get_random_submission_zip()

        async with event(self, "[UI] Submit task"):
            await page.get_by_text("My Submissions").click()
            with page.expect_file_chooser() as fc_info:
                await page.get_by_role("button", name="").click()
            file_chooser = fc_info.value
            file_chooser.set_files(submission)
        expect(page.locator(".ui.indicating")).to_be_visible()
        expect(page.locator(".ui.indicating")).not_to_be_visible()
        # Wait for the run to be completed (Finished or Failed) to show.
        # "Failed" regex is more flexible because the cell also contain a question mark
        finished_or_failed = re.compile(r"^(Finished|Failed.*)$")
        try:
            expect(page.get_by_role("cell", name=finished_or_failed)).to_be_visible(
                timeout=25000
            )
        # If it does not, catch the error and reload the page in case the page didn't update automatically
        except Exception:
            page.reload()
            expect(page.get_by_role("cell", name=finished_or_failed)).to_be_visible(
                timeout=2000
            )
        # Then we actually check if we got the expected result

        try:
            expect(page.get_by_role("cell", name="Finished")).to_be_visible()
            # Add to leaderboard and see if shows
            text = page.locator(".submission_row").first.inner_text()
            submission_id = text.split(None, 1)
            try:
                page.locator("td:nth-child(6) > span > .icon").first.click(timeout=300)
            except Exception:
                page.locator("td:nth-child(7) > span > .icon").first.click(timeout=300)
            page.locator("div").filter(has_text=re.compile(r"^Results$")).click()
            expect(
                page.locator("#leaderboardTable").get_by_role(
                    "link", name=self.codabench_user.username
                )
            ).to_be_visible()
            expect(
                page.get_by_role("cell", name=submission_id[0], exact=True)
            ).to_be_visible()
        except Exception as e:
            raise ValueError(
                f"Unexpected submission status for submission_id={submission_id[0]!r}. {e}"
                "Expected 'Finished'."
            ) from e
