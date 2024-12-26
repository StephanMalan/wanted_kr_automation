from dataclasses import dataclass
from typing import Any


import requests

from wanted import Terminal


class RequestError(ValueError):
    def __init__(self, url: str, status_code: int, error_text: str) -> None:
        super().__init__(url, status_code, error_text)


BASE_URL = "https://www.wanted.co.kr"


@dataclass
class Session:
    token: str
    expiry: int

    @staticmethod
    def from_token(token: str, expiry: int) -> "Session":
        return Session(token, expiry)

    @staticmethod
    def from_credentials(email: str, password: str) -> "Session":
        token, expiry = Session._login(email, password)
        return Session(token, expiry)

    @classmethod
    def _login(cls, email: str, password: str) -> tuple[str, int]:
        with Terminal.LoadTask("Logging in") as task:
            data = cls._make_request(
                "post",
                "https://id-api.wanted.jobs/v1/auth/token",
                json={
                    "grant_type": "password",
                    "email": email,
                    "password": password,
                    "client_id": "AhWBZolyUalsuJpHVRDrE4Px",
                    "redirect_url": f"{BASE_URL}/api/chaos/auths/v1/callback/set-token",
                },
            )
            token: str = data["token"]
            expiry: int = data["expires"]
            task.success("Logged in")
            return (token, expiry)

    def get_request(self, url: str, json: dict[str, Any] | None = None) -> dict[str, Any]:
        return self._make_session_request("get", url, json=json)

    def post_request(self, url: str, json: dict[str, Any] | None = None) -> dict[str, Any]:
        return self._make_session_request("post", url, json=json)

    def put_request(self, url: str, json: dict[str, Any] | None = None) -> dict[str, Any]:
        return self._make_session_request("put", url, json=json)

    def _make_session_request(self, method: str, url: str, json: dict[str, Any] | None = None) -> dict[str, Any]:
        headers = {"Cookie": f"WWW_ONEID_ACCESS_TOKEN={self.token}"}
        return self._make_request(method, url, headers=headers, json=json)

    @staticmethod
    def _make_request(
        method: str, url: str, headers: dict[str, Any] | None = None, json: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        response = requests.request(method, url, json=json, headers=headers, timeout=20)
        if response.status_code != 200:
            raise RequestError(url, response.status_code, response.text)
        resp: dict[str, Any] = response.json()
        return resp
