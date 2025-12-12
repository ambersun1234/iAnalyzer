from typing import List, Set
from urllib.parse import urljoin, urlparse

from playwright.sync_api import BrowserContext

from src.logger.logger import logger


class Crawler:
    def __init__(
        self,
        domain: str,
        context: BrowserContext,
        max_pages: int = 1000000,
        ignore_prefixes: list = None,
    ):
        self.domain = domain
        self.context = context
        self.max_pages = max_pages
        self.ignore_prefixes = ignore_prefixes or []
        self.visited: Set[str] = set()
        self.to_visit: List[str] = [domain]

    def _should_ignore(self, url: str) -> bool:
        for prefix in self.ignore_prefixes:
            if url.startswith(prefix):
                return True
        return False

    def discover_pages(self) -> List[str]:
        sitemap_pages = self._try_sitemap()
        if sitemap_pages:
            self.to_visit.extend(sitemap_pages)
            self.visited.update(sitemap_pages)

        while self.to_visit and len(self.visited) < self.max_pages:
            url = self.to_visit.pop(0)
            if url in self.visited:
                continue
            if self._should_ignore(url):
                logger.debug(f"Skipping ignored URL: {url}")
                continue

            try:
                page = self.context.new_page()
                try:
                    response = page.goto(url, wait_until="load", timeout=90000)
                except Exception:
                    try:
                        response = page.goto(
                            url, wait_until="domcontentloaded", timeout=60000
                        )
                    except Exception:
                        logger.debug(f"Timeout loading {url}, skipping")
                        page.close()
                        continue

                if response and response.status == 200:
                    final_url = page.url
                    if final_url.startswith(self.domain) and not self._should_ignore(
                        final_url
                    ):
                        self.visited.add(final_url)
                        links = self._extract_links(page)
                        for link in links:
                            if (
                                link not in self.visited
                                and link not in self.to_visit
                                and not self._should_ignore(link)
                            ):
                                self.to_visit.append(link)

                page.close()

            except Exception as e:
                logger.debug(f"Failed to crawl {url}: {e}")
                try:
                    page.close()
                except:
                    pass

        return list(self.visited)

    def _try_sitemap(self) -> List[str]:
        sitemap_urls = [
            f"{self.domain}/sitemap.xml",
            f"{self.domain}/sitemap_index.xml",
            f"{self.domain}/sitemap.txt",
        ]

        for sitemap_url in sitemap_urls:
            try:
                page = self.context.new_page()
                response = page.goto(sitemap_url, timeout=10000)

                if response and response.status == 200:
                    content = page.content()
                    urls = self._parse_sitemap(content, sitemap_url)
                    page.close()
                    if urls:
                        return [
                            url
                            for url in urls
                            if url.startswith(self.domain)
                            and not self._should_ignore(url)
                        ]
                page.close()
            except:
                pass

        return []

    def _parse_sitemap(self, content: str, base_url: str) -> List[str]:
        urls = []

        if "<?xml" in content or "<urlset" in content:
            import re

            locs = re.findall(r"<loc>(.*?)</loc>", content, re.IGNORECASE)
            urls.extend(locs)
        else:
            for line in content.split("\n"):
                line = line.strip()
                if line and line.startswith("http"):
                    urls.append(line)

        return urls

    def _extract_links(self, page) -> List[str]:
        links = []

        try:
            anchors = page.query_selector_all("a[href]")
            for anchor in anchors:
                href = anchor.get_attribute("href")
                if not href:
                    continue

                href_lower = href.lower().strip()
                if href_lower.startswith(
                    ("mailto:", "tel:", "javascript:", "data:", "file:", "ftp:")
                ):
                    continue

                absolute_url = urljoin(page.url, href).split("#")[0]

                if absolute_url.startswith(self.domain):
                    links.append(absolute_url)

        except Exception as e:
            logger.debug(f"Error extracting links: {e}")

        return links
