import sys
import time
from concurrent.futures import ThreadPoolExecutor
from itertools import chain, repeat

from src.config import Config, JobType
from src.http_request import RequestError, get_request, post_request, put_request
from src.logging import ProgressBar, Spinner, log_task_fail
from src.session import SessionData

BASE_URL = "https://www.wanted.co.kr"


def retrieve_listings(config: Config, session_data: SessionData) -> list[int]:
    spinner = Spinner("Retrieving listings")
    try:
        with ThreadPoolExecutor() as executor:
            results = executor.map(_retrieve_job_type_listings, config.searches.items(), repeat(session_data))
            listings = list(set(list(chain.from_iterable(results))))
        if not listings:
            spinner.stop("No new listings found", successful=False)
            sys.exit(0)
        spinner.stop(f"Retrieved {len(list(listings))} listings")
        return listings
    except RequestError:
        spinner.stop("Failed to retrieve listings", successful=False)
        sys.exit(1)


def filter_listings(listings: list[int], config: Config, session_data: SessionData) -> list[int]:
    try:
        with ThreadPoolExecutor() as executor:
            filter_results = list(
                ProgressBar(
                    executor.map(_filter_listing, listings, repeat(config), repeat(session_data)),
                    "Filtering listings",
                    "Succesfully filtered {num} listings",
                    "No suitable listings found",
                    total=len(listings),
                )
            )
    except RequestError:
        log_task_fail("Failed to filter listings")
        sys.exit(1)
    return list(set(listing_id for listing_id in filter_results if listing_id is not None))


def apply_to_listings(listings: list[int], session_data: SessionData) -> None:
    try:
        with ThreadPoolExecutor() as executor:
            _ = list(
                ProgressBar(
                    executor.map(_apply_to_listing, listings, repeat(session_data)),
                    "Applying to listings",
                    "Successfully applied to {num} listings",
                    "Failed to apply to any listings",
                    total=len(listings),
                )
            )
    except RequestError:
        log_task_fail("Failed to apply to listings")
        sys.exit(1)


def _retrieve_job_type_listings(job_search: tuple[JobType, int], session_data: SessionData) -> list[int]:
    url = (
        f"{BASE_URL}/api/v4/jobs?{int(time.time())}"
        "&country=kr"
        f"&tag_type_id={job_search[0].value}"
        "&job_sort=job.latest_order"
        "&limit=100"
        f"&years={job_search[1]}"
    )
    listings: list[int] = []
    while url:
        data = get_request(url, token=session_data.token)
        url_affix = data["links"]["next"]
        url = f"{BASE_URL}{url_affix}" if url_affix else url_affix
        for listing in data["data"]:
            if not listing["is_bookmark"]:
                listings.append(listing["id"])
    return listings


def _filter_listing(listing_id: int, config: Config, session_data: SessionData) -> int | None:
    data = get_request(f"{BASE_URL}/api/v4/jobs/{listing_id}", token=session_data.token)
    if data["application"]:
        if not data["job"]["is_bookmark"]:
            _bookmark(listing_id, session_data)
        return None
    details = data["job"]["detail"]
    desc = f'{details["requirements"]}\n{details["main_tasks"]}\n{details["intro"]}\n{details["preferred_points"]}'
    if any(bl_word in desc for bl_word in config.filter_words):
        return None
    if any(req_word in desc for req_word in config.required_words):
        return listing_id
    return None if config.required_words else listing_id


def _apply_to_listing(listing_id: int, session_data: SessionData) -> None:
    instance_id = _init_application(listing_id, session_data)
    _apply(instance_id, session_data)
    _bookmark(listing_id, session_data)


def _init_application(listing_id: int, session_data: SessionData) -> str:
    data = post_request(
        f"{BASE_URL}/api/v3/applications?{int(time.time())}",
        json={"email": session_data.email, "job_id": listing_id, "name": session_data.name},
        token=session_data.token,
    )
    instance_id: str = data["id"]
    return instance_id


def _apply(instance_id: str, session_data: SessionData) -> None:
    put_request(
        f"{BASE_URL}/api/v3/applications/{instance_id}?{int(time.time())}",
        json={
            "email": session_data.email,
            "name": session_data.name,
            "mobile": session_data.mobile,
            "resumes": [{"key": session_data.resume_id, "type": "pdf"}],
        },
        token=session_data.token,
    )


def _bookmark(listing_id: int, session_data: SessionData) -> None:
    data = post_request(
        f"{BASE_URL}/api/chaos/bookmarks/v1/{listing_id}?{int(time.time())}",
        token=session_data.token,
    )
    assert data["flag"]
