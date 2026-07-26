from locust import task
from locust_plugins.users.playwright import PageWithRetry, PlaywrightUser, event, pw


class UIUser(PlaywrightUser):

    @task
    @pw
    async def check_submit_button(self, page: PageWithRetry):
        async with event(self, "Load competition page"):
            await page.goto("/competitions/1")
        await page.click('button:has-text("Submit")')
