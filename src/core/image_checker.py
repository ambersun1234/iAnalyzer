from playwright.sync_api import BrowserContext

from src.logger.logger import logger


class ImageChecker:
    def __init__(self, context: BrowserContext, ignore_prefixes: list = None):
        self.context = context
        self.ignore_prefixes = ignore_prefixes or []

    def _should_ignore(self, url: str) -> bool:
        for prefix in self.ignore_prefixes:
            if url.startswith(prefix):
                return True
        return False

    def check_page(self, page_url: str) -> bool:
        fail = False
        try:
            if self._should_ignore(page_url):
                logger.debug(f"Skipping ignored page: {page_url}")
                return

            page = self.context.new_page()
            try:
                response = page.goto(page_url, wait_until="load", timeout=90000)
            except Exception:
                try:
                    response = page.goto(
                        page_url, wait_until="domcontentloaded", timeout=60000
                    )
                except Exception:
                    logger.debug(f"Timeout loading {page_url}, skipping")
                    raise

            if not response or response.status != 200:
                return

            page.wait_for_timeout(2000)

            images = page.query_selector_all("img")
            for img in images:
                logger.debug(f"Checking image: {img.get_attribute('src')}")
                self._check_image(img, page_url)
        except Exception as e:
            fail = True
            logger.error(
                f"Error checking page", extra={"page_url": page_url, "error": e}
            )
        finally:
            page.close() if page else None

        return fail

    def _check_image(self, img_element, page_url: str):
        try:
            img_url = img_element.evaluate(
                """(img) => {
                return img.currentSrc || img.src || '';
            }"""
            )

            if not img_url:
                return

            box = img_element.bounding_box()
            if not box:
                self._log_invalid(img_url, page_url, "No bounding box")
                return

            width = box.get("width", 0)
            height = box.get("height", 0)

            natural_size = img_element.evaluate(
                """(img) => {
                return {
                    naturalWidth: img.naturalWidth,
                    naturalHeight: img.naturalHeight,
                    complete: img.complete
                };
            }"""
            )

            natural_width = natural_size.get("naturalWidth", 0)
            natural_height = natural_size.get("naturalHeight", 0)

            if width == 0 and height == 0:
                logger.error(
                    f"Rendered size is 0x0",
                    extra={
                        "page_url": page_url,
                        "img_url": img_url,
                        "reason": "Rendered size is 0x0",
                    },
                )
                raise Exception("Rendered size is 0x0")

            elif natural_width == 0 and natural_height == 0:
                logger.error(
                    f"Image failed to load (natural size 0x0)",
                    extra={
                        "page_url": page_url,
                        "img_url": img_url,
                        "reason": "Image failed to load (natural size 0x0)",
                    },
                )
                raise Exception("Image failed to load (natural size 0x0)")

        except Exception as e:
            logger.debug(
                f"Error checking image",
                extra={"page_url": page_url, "img_url": img_url, "error": e},
            )
            raise e
