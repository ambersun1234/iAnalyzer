from playwright.sync_api import sync_playwright

from src.core.crawler import Crawler
from src.core.image_checker import ImageChecker
from src.logger.logger import logger


class ImageAnalyzer:
    def __init__(self, domain: str, ignore_prefixes: list = None):
        domain = domain.rstrip("/")
        if not domain.startswith(("http://", "https://")):
            domain = "https://" + domain
        self.domain = domain
        self.ignore_prefixes = ignore_prefixes or []

    def _should_ignore(self, url: str) -> bool:
        for prefix in self.ignore_prefixes:
            if url.startswith(prefix):
                return True
        return False

    def analyze(self) -> int:
        fail_count = 0

        site_results = []
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                viewport={"width": 1920, "height": 1080},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            )

            try:
                crawler = Crawler(
                    self.domain, context, ignore_prefixes=self.ignore_prefixes
                )
                pages = crawler.discover_pages()
                logger.info(
                    f"Found {len(pages)} pages to analyze",
                    extra={"domain": self.domain},
                )

                checker = ImageChecker(context, ignore_prefixes=self.ignore_prefixes)
                for index, page_url in enumerate(pages):
                    logger.info(
                        f"Checking page...",
                        extra={
                            "page_url": page_url,
                            "index": index + 1,
                            "total": len(pages),
                        },
                    )
                    if self._should_ignore(page_url):
                        logger.warning(
                            f"Skipping ignored page", extra={"page_url": page_url}
                        )
                        continue

                    page_result, page_fail_count = checker.check_page(page_url)
                    fail_count += page_fail_count
                    site_results.extend(page_result)
            except Exception as e:
                logger.error(
                    f"Error analyzing page", extra={"page_url": page_url, "error": e}
                )

            finally:
                context.close()
                browser.close()

        logger.info("Analyze finished.", extra={"results": site_results})

        return fail_count
