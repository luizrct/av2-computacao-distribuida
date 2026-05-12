import itertools
import os
import re
from pathlib import Path

from locust import HttpUser, constant, task, between


URLS_FILE = Path("/mnt/urls.txt")
REQUEST_MODE = os.getenv("REQUEST_MODE", "distributed").lower()

VALID_REQUEST_MODES = {
    "aggregated",
    "distributed",
}


def normalize_alias(alias: str) -> str:
    alias = alias.strip().lower()
    alias = re.sub(r"[^a-z0-9_-]", "_", alias)
    return alias


def load_urls():
    urls = []

    with open(URLS_FILE, "r", encoding="utf-8") as file:
        for line in file:
            line = line.strip()

            if not line or line.startswith("#"):
                continue

            alias, url = line.split("=", 1)

            urls.append({
                "alias": normalize_alias(alias),
                "url": url.strip(),
            })

    return urls


URLS = load_urls()

URL_CYCLE = itertools.cycle(URLS)


class LinkExtractorUser(HttpUser):
    wait_time = between(1, 3)

    @task
    def extract_links(self):
        item = next(URL_CYCLE)

        alias = item["alias"]
        url = item["url"]

        request_name = (
            "extract_links"
            if REQUEST_MODE == "aggregated"
            else f"extract_links_{alias}"
        )

        with self.client.get(
            "/api/",
            params={"url": url},
            name=request_name,
            catch_response=True,
        ) as response:

            if response.status_code >= 400:
                response.failure(
                    f"HTTP {response.status_code}: {response.text[:300]}"
                )