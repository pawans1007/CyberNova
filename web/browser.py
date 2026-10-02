import ipaddress
import socket
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup


class WebPageReader:
    USER_AGENT = (
        "CyberNovaResearch/1.0 "
        "(public webpage text retrieval)"
    )

    MAX_BYTES = 1_000_000
    MAX_REDIRECTS = 5

    def _validate_url(self, url):
        parsed = urlparse(url)

        if parsed.scheme not in ("http", "https"):
            raise ValueError("Only HTTP and HTTPS URLs are allowed.")

        if not parsed.hostname:
            raise ValueError("The URL must contain a hostname.")

        hostname = parsed.hostname.lower()

        if hostname in ("localhost", "localhost.localdomain"):
            raise ValueError("Localhost URLs are not allowed.")

        try:
            addresses = {
                item[4][0]
                for item in socket.getaddrinfo(
                    hostname,
                    parsed.port or (
                        443 if parsed.scheme == "https" else 80
                    ),
                    type=socket.SOCK_STREAM,
                )
            }
        except socket.gaierror as error:
            raise ValueError(
                f"Could not resolve hostname: {error}"
            ) from error

        if not addresses:
            raise ValueError("The hostname did not resolve.")

        for address in addresses:
            ip = ipaddress.ip_address(address)

            if not ip.is_global:
                raise ValueError(
                    "Private, local, and non-public IP destinations "
                    "are not allowed."
                )

        return url

    def read(self, url):
        current_url = str(url).strip()

        if not current_url:
            return {
                "success": False,
                "error": "URL cannot be empty.",
            }

        headers = {
            "User-Agent": self.USER_AGENT,
            "Accept": "text/html,text/plain",
        }

        try:
            response = None

            for _ in range(self.MAX_REDIRECTS + 1):
                self._validate_url(current_url)

                response = requests.get(
                    current_url,
                    headers=headers,
                    timeout=(5, 15),
                    stream=True,
                    allow_redirects=False,
                )

                if response.is_redirect or response.is_permanent_redirect:
                    location = response.headers.get("Location")
                    response.close()

                    if not location:
                        raise ValueError(
                            "Redirect response has no destination."
                        )

                    current_url = urljoin(
                        current_url,
                        location,
                    )
                    continue

                break
            else:
                raise ValueError("Too many redirects.")

            if response is None:
                raise ValueError("No response was received.")

            with response:
                response.raise_for_status()

                content_type = response.headers.get(
                    "Content-Type",
                    "",
                ).lower()

                if not (
                    "text/html" in content_type
                    or "text/plain" in content_type
                ):
                    raise ValueError(
                        "Only HTML and plain-text pages are supported."
                    )

                chunks = []
                total_size = 0

                for chunk in response.iter_content(
                    chunk_size=8192
                ):
                    if not chunk:
                        continue

                    total_size += len(chunk)

                    if total_size > self.MAX_BYTES:
                        raise ValueError(
                            "Page exceeds the 1 MB retrieval limit."
                        )

                    chunks.append(chunk)

                raw_content = b"".join(chunks)
                encoding = response.encoding or "utf-8"
                html = raw_content.decode(
                    encoding,
                    errors="replace",
                )

            if "text/plain" in content_type:
                text = html
                title = current_url
            else:
                soup = BeautifulSoup(
                    html,
                    "html.parser",
                )

                for element in soup(
                    ["script", "style", "noscript", "svg"]
                ):
                    element.decompose()

                title = (
                    soup.title.get_text(strip=True)
                    if soup.title
                    else current_url
                )

                text = soup.get_text(
                    separator="\n",
                    strip=True,
                )

            return {
                "success": True,
                "url": current_url,
                "title": title,
                "text": text[:20000],
            }

        except Exception as error:
            return {
                "success": False,
                "error": str(error),
            }