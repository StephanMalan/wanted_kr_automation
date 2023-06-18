import sys
import time
from dataclasses import dataclass

from src.http_request import RequestError, get_request, post_request
from src.logging import Spinner

BASE_URL = "https://www.wanted.co.kr"


@dataclass
class SessionData:
    token: str
    email: str
    name: str
    mobile: str
    resume_id: str


def login(email: str, password: str) -> tuple[str, int]:
    spinner = Spinner("Logging in")
    try:
        data = post_request(
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
        spinner.stop("Logged in")
        return (token, expiry)
    except RequestError:
        spinner.stop("Failed to log in", successful=False)
        sys.exit(1)


def get_session_data(token: str) -> SessionData:
    spinner = Spinner("Retrieving user details")
    try:
        data = get_request("https://id-api.wanted.jobs/v1/me", token=token)
        user = data["user"]
        email: str = user["email"]
        name: str = user["username"]
        mobile: str = user["mobile"]["number"]

        data = get_request(f"https://www.wanted.co.kr/api/chaos/resumes/v1?{int(time.time())}", token=token)
        resumes = data["data"]
        assert len(resumes)
        resume_id: str = resumes[0]["key"]

        spinner.stop("Retrieved user details")
        return SessionData(token, email, name, mobile, resume_id)
    except RequestError:
        spinner.stop("Failed to retrieve user details", successful=False)
        sys.exit(1)
