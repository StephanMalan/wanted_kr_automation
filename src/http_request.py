from typing import Any

import requests


class RequestError(ValueError):
    def __init__(self, url: str, status_code: int, error_text: str) -> None:
        super().__init__(url, status_code, error_text)


def get_request(url: str, json: dict[str, Any] | None = None, token: str | None = None) -> dict[str, Any]:
    return _make_request("get", url, json=json, token=token)


def post_request(url: str, json: dict[str, Any] | None = None, token: str | None = None) -> dict[str, Any]:
    return _make_request("post", url, json=json, token=token)


def put_request(url: str, json: dict[str, Any] | None = None, token: str | None = None) -> dict[str, Any]:
    return _make_request("put", url, json=json, token=token)


def _make_request(
    method: str, url: str, json: dict[str, Any] | None = None, token: str | None = None
) -> dict[str, Any]:
    headers = {"Cookie": f"WWW_ONEID_ACCESS_TOKEN={token}"} if token else None
    response = requests.request(method, url, json=json, headers=headers, timeout=10)
    if response.status_code != 200:
        raise RequestError(url, response.status_code, response.text)
    data: dict[str, Any] = response.json()
    return data
