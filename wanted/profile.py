from __future__ import annotations

import time
from dataclasses import dataclass
from typing import TYPE_CHECKING

from wanted import BASE_URL, Terminal

if TYPE_CHECKING:
    from wanted import Session


@dataclass
class ProfileData:
    email: str
    name: str
    mobile: str
    resume_id: str

    @staticmethod
    def get_session_data(session: Session) -> ProfileData:
        with Terminal.LoadTask("Retrieving user details") as task:
            data = session.get_request("https://id-api.wanted.jobs/v1/me")
            user = data["user"]
            email: str = user["email"]
            name: str = user["username"]
            mobile: str = user["mobile"]["number"]

            data = session.get_request(f"{BASE_URL}/api/chaos/resumes/v1?{int(time.time())}")
            resumes = data["data"]
            assert len(resumes)
            resume_id: str = resumes[0]["key"]

            task.success("Retrieved user details")
            return ProfileData(email, name, mobile, resume_id)
