from locust.clients import HttpSession


def authenticate(client: HttpSession, username: str, password: str):
    response = client.post(
        "/api/api-token-auth/", json={"username": username, "password": password}
    )
    response.raise_for_status()
    client.headers.update({"Authorization": f"Token {response.json()['token']}"})
