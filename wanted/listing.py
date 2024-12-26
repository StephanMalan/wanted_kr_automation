from __future__ import annotations

import sys
import time
from concurrent.futures import ThreadPoolExecutor
from itertools import chain, repeat
from typing import Any, TYPE_CHECKING

from wanted import Terminal, BASE_URL, RequestError

if TYPE_CHECKING:
    from wanted import Session, Config, JobType, ProfileData


class Listing:
    @staticmethod
    def retrieve_listings(config: Config, session: Session) -> list[int]:
        with Terminal.LoadTask("Retrieving listings") as spinner:
            with ThreadPoolExecutor() as executor:
                results = executor.map(_retrieve_job_listings, config.searches.items(), repeat(session))
                listings = list(set(list(chain.from_iterable(results))))
            if not listings:
                spinner.fail("No new listings found")
                sys.exit(0)
            spinner.success(f"Retrieved {len(list(listings))} listings")
            return listings

    @staticmethod
    def filter_listings(listings: list[int], session: Session) -> list[int]:
        try:
            with ThreadPoolExecutor() as executor:
                filter_results: list[int | None] = list(
                    Terminal.ProgressBar(
                        executor.map(_filter_listing, listings, repeat(session)),
                        "Filtering listings",
                        "Succesfully filtered {num} listings",
                        "No suitable listings found",
                        total=len(listings),
                    )
                )
        except RequestError:
            Terminal.log_task_fail("Failed to filter listings")
            sys.exit(1)
        return list(set(listing_id for listing_id in filter_results if listing_id is not None))

    @staticmethod
    def apply_to_listings(listings: list[int], session: Session, profile_data: ProfileData) -> None:
        try:
            with ThreadPoolExecutor() as executor:
                _: Any = list(
                    Terminal.ProgressBar(
                        executor.map(_apply_to_listing, listings, repeat(session), repeat(profile_data)),
                        "Applying to listings",
                        "Successfully applied to {num} listings",
                        "Failed to apply to any listings",
                        total=len(listings),
                    )
                )
        except RequestError:
            Terminal.log_task_fail("Failed to apply to listings")
            sys.exit(1)


def _retrieve_job_listings(job_search: tuple[JobType, int], session: Session) -> list[int]:
    url = (
        f"{BASE_URL}/api/v4/jobs?{int(time.time())}"
        "&country=kr"
        f"&tag_type_id={job_search[0].value}"
        "&job_sort=job.latest_order"
        "&limit=100"
        "&years=0"
        f"&years={job_search[1]}"
    )
    listings: list[int] = []
    while url:
        data = session.get_request(url)
        url_affix = data["links"]["next"]
        url = f"{BASE_URL}{url_affix}" if url_affix else url_affix
        for listing in data["data"]:
            if not listing["is_bookmark"]:
                listings.append(listing["id"])
    return listings


def _filter_listing(listing_id: int, session: Session) -> int | None:
    data = session.get_request(f"{BASE_URL}/api/v4/jobs/{listing_id}")
    if data["application"]:
        if not data["job"]["is_bookmark"]:
            _bookmark(listing_id, session)
        return None
    return listing_id


def _apply_to_listing(listing_id: int, session: Session, profile_data: ProfileData) -> None:
    instance_id = _init_application(listing_id, session, profile_data)
    _apply(instance_id, session, profile_data)
    _bookmark(listing_id, session)


def _init_application(listing_id: int, session: Session, profile_data: ProfileData) -> str:
    data = session.post_request(
        f"{BASE_URL}/api/v3/applications?{int(time.time())}",
        json={"email": profile_data.email, "job_id": listing_id, "name": profile_data.name},
    )
    instance_id: str = data["id"]
    return instance_id


def _apply(instance_id: str, session: Session, profile_data: ProfileData) -> None:
    session.put_request(
        f"{BASE_URL}/api/v3/applications/{instance_id}?{int(time.time())}",
        json={
            "email": profile_data.email,
            "name": profile_data.name,
            "mobile": profile_data.mobile,
            "resumes": [{"key": profile_data.resume_id, "type": "pdf"}],
        },
    )


def _bookmark(listing_id: int, session: Session) -> None:
    data = session.post_request(f"{BASE_URL}/api/chaos/bookmarks/v1/{listing_id}?{int(time.time())}")
    assert data["flag"]
