import datetime as dt
import json
from enum import Enum
from typing import Optional

import pytz
from pydantic import BaseModel


class JobType(str, Enum):
    PYTHON = "899"
    JAVA = "660"


class Config(BaseModel):
    email: str
    token: str | None
    token_exp: int | None
    cache_token: bool
    searches: dict[JobType, int]
    filter_words: list[str]
    required_words: list[str]

    @classmethod
    def load_from_file(cls) -> Optional["Config"]:
        try:
            with open("config.json", "r", encoding="utf-8") as file:
                data = json.load(file)
                cfg = Config(**data)
                cfg._validate_token_caching()
                return cfg
        except FileNotFoundError:
            return None

    def save_to_file(self) -> None:
        with open("config.json", "w", encoding="utf-8") as file:
            file.write(json.dumps(self, default=lambda x: x.__dict__, indent=4))

    def cache_token_data(self, token: str, expiry: int) -> None:
        if not self.cache_token:
            return
        self.token = token
        self.token_exp = expiry
        self.save_to_file()

    def check_token_validity(self) -> bool:
        if not self.token or not self.token_exp:
            return False
        expiry_dt = dt.datetime.fromtimestamp(self.token_exp, tz=pytz.timezone("Asia/Seoul"))
        return expiry_dt - dt.datetime.now().astimezone() > dt.timedelta(hours=1)

    def _validate_token_caching(self) -> None:
        if not self.cache_token and (self.token or self.token_exp):
            self.token = None
            self.token_exp = None
            self.save_to_file()
