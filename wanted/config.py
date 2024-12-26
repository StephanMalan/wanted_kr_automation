from __future__ import annotations

from datetime import timezone, timedelta, datetime
import json
from enum import Enum
from typing import TYPE_CHECKING

from pydantic import BaseModel

if TYPE_CHECKING:
    from wanted import Session

KOREA_TZ = timezone(timedelta(hours=9))  # UTC+9 for Asia/Seoul
CONFIG_FILE = "config.json"


class JobType(str, Enum):
    JAVA = "660"
    NODE = "518"
    PYTHON = "899"
    WEB = "873"


class Config(BaseModel):
    email: str
    token: str | None
    token_exp: int | None
    cache_token: bool
    searches: dict[JobType, int]

    @classmethod
    def load_from_file(cls) -> Config | None:
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as cfg_file:
                data = json.load(cfg_file)
                cfg = Config(**data)
                cfg._validate_token_caching()
                return cfg
        except FileNotFoundError:
            return None

    def save_to_file(self) -> None:
        with open("config.json", "w", encoding="utf-8") as file:
            file.write(json.dumps(self, default=lambda x: x.__dict__, indent=4))

    def cache_session(self, session: Session) -> None:
        if not self.cache_token:
            return
        self.token = session.token
        self.token_exp = session.expiry
        self.save_to_file()

    def check_token_validity(self) -> bool:
        if not self.token_exp:
            return False
        expiry_dt = datetime.fromtimestamp(self.token_exp, tz=KOREA_TZ)
        return expiry_dt - datetime.now().astimezone() > timedelta(hours=1)

    def _validate_token_caching(self) -> None:
        if not self.cache_token and (self.token or self.token_exp):
            self.token = None
            self.token_exp = None
            self.save_to_file()
