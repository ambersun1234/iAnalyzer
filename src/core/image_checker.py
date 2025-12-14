from playwright.sync_api import BrowserContext

from src.logger.logger import logger


class ImageChecker:
    def __init__(self, context: BrowserContext, ignore_prefixes: list = None):
        self.context = context
        self.ignore_prefixes = ignore_prefixes or []

    def check_page(self, page_url: str) -> bool:
        fail = False
        try:
            page = self.context.new_page()
            try:
                response = page.goto(page_url, wait_until="load", timeout=90000)
            except Exception:
                logger.debug(f"Timeout loading {page_url}, skipping")
                raise

            if not response or response.status != 200:
                logger.warning(
                    f"Page loaded with error",
                    extra={"status": response.status or "unknown"},
                )
                raise Exception(f"Failed to load page: {page_url}")

            images = page.query_selector_all("img")
            for index, img in enumerate(images):
                logger.debug(
                    f"Checking image",
                    extra={
                        "img_url": img.get_attribute("src"),
                        "index": index + 1,
                        "total": len(images),
                    },
                )
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
            img_url = img_element.get_attribute("src")

            box = img_element.bounding_box()
            if not box:
                logger.error(
                    f"No bounding box",
                    extra={
                        "page_url": page_url,
                        "img_url": img_url,
                        "reason": "No bounding box",
                    },
                )
                return

            width = img_element.get_attribute("width")
            height = img_element.get_attribute("height")

            if width == 0 or height == 0:
                logger.error(
                    f"Image failed to load (size 0)",
                    extra={
                        "page_url": page_url,
                        "img_url": img_url,
                        "reason": "Image failed to load (size 0)",
                    },
                )
                raise Exception("Image failed to load (size 0)")

        except Exception as e:
            raise e
