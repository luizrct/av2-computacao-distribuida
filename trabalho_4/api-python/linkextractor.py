from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup


def extract_links(url: str) -> list[str]:
    response = requests.get(url, timeout=10)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    links = []

    for tag in soup.find_all("a", href=True):
        href = tag.get("href")

        if href:
            links.append(urljoin(url, href))

    return sorted(set(links))