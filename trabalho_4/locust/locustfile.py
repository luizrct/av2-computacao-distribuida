import os
import re
from pathlib import Path

from locust import HttpUser, constant, between, task


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

            if "=" not in line:
                raise ValueError(f"Linha inválida no urls.txt: {line}")

            alias, url = line.split("=", 1)

            alias = normalize_alias(alias)
            url = url.strip()

            urls.append({
                "alias": alias,
                "url": url,
            })

    if len(urls) < 10:
        raise ValueError("O arquivo urls.txt precisa ter pelo menos 10 URLs.")

    return urls


URLS = load_urls()


if REQUEST_MODE not in VALID_REQUEST_MODES:
    raise ValueError(
        f"REQUEST_MODE inválido: {REQUEST_MODE}. "
        f"Use: {', '.join(VALID_REQUEST_MODES)}"
    )


class LinkExtractorUser(HttpUser):
    wait_time = constant(0)
    @task
    def extract_links_sequence(self):
        for item in URLS[:10]:
            alias = item["alias"]
            url = item["url"]

            request_name = (
                "extract_links"
                if REQUEST_MODE == "aggregated"
                else f"extract_links_{alias}"
            )

            with self.client.get(
                "/api",
                params={"url": url},
                name=request_name,
                catch_response=True,
            ) as response:
                if response.status_code >= 400:
                    response.failure(
                        f"HTTP {response.status_code}: {response.text[:300]}"
                    )