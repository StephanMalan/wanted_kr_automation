from __future__ import annotations

import re

from src.config import Config, JobType


def prompt_user_for_config() -> Config:
    email_regex = r"([A-Za-z0-9]+[.-_])*[A-Za-z0-9]+@[A-Za-z0-9-]+(\.[A-Z|a-z]{2,})+"
    email = _prompt_regex("Enter your wanted.co.kr email", email_regex)

    cache_token = _prompt_question("Would you like to cache your token between runs")

    searches: dict[JobType, int] = {}
    # pylint: disable=protected-access, no-member
    job_types_options = [job_type.lower() for job_type in JobType._member_names_]
    while True:
        if not _prompt_question("Would you like to add a job search"):
            break
        job_type = _prompt_option("Choose the job type", job_types_options)
        years_exp = _prompt_regex(f"Your years of experience with {job_type.title()}", r"^([0-2]?[0-9]|30)$")
        searches[getattr(JobType, job_type.upper())] = int(years_exp)

    filter_words: list[str] = []
    while _prompt_question("Would you like to add a filter word"):
        filter_words.append(input("  Please enter your filter word: "))

    required_words: list[str] = []
    while True:
        if not _prompt_question("  Would you like to add a required word [Y/N]: "):
            break
        required_words.append(input("  Please enter your required word: "))

    return Config(
        email=email,
        token=None,
        token_exp=None,
        cache_token=cache_token,
        searches=searches,
        filter_words=filter_words,
        required_words=required_words,
    )


def _prompt_question(text: str) -> bool:
    option = _prompt_option(text, ["y", "n"])
    return option in ["y"]


def _prompt_option(text: str, options: list[str]) -> str:
    while True:
        user_input = input(f"  {text} [{'/'.join(options)}]: ")
        if user_input.lower() in options:
            return user_input.lower()


def _prompt_regex(text: str, regex: str) -> str:
    while True:
        user_input = input(f"  {text}: ")
        if re.match(regex, user_input):
            return user_input
