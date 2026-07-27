from __future__ import annotations

from locust_plugins.users.playwright import PageWithRetry


async def login(page: PageWithRetry, username: str, password: str) -> None:
    await page.goto("/")
    await page.get_by_role("link", name="Login").click()
    await page.get_by_role("textbox", name="username or email").click()
    await page.get_by_role("textbox", name="username or email").fill(username)
    await page.get_by_role("textbox", name="password").click()
    await page.get_by_role("textbox", name="password").fill(password)
    await page.get_by_role("button", name="Log In").click()
