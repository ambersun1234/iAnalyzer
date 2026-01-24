from playwright.sync_api import BrowserContext, Locator

from src.logger.logger import logger


class ImageChecker:
    def __init__(self, context: BrowserContext, ignore_prefixes: list = None):
        self.context = context
        self.ignore_prefixes = ignore_prefixes or []

    def check_page(self, page_url: str) -> (list, bool):
        fail = False

        page_fail_results = []
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

            images = page.locator("img").all()
            for index, img in enumerate(images):
                width, height = self._check_image(img, page_url)
                logger.debug(
                    f"Checking image",
                    extra={
                        "img_url": img.get_attribute("src"),
                        "metadata": {
                            "width": width,
                            "height": height,
                        },
                        "index": index + 1,
                        "total": len(images),
                    },
                )

        except Exception as e:
            fail = True
            logger.error(
                f"Error checking page", extra={"page_url": page_url, "error": e}
            )
            page_fail_results.append(
                {
                    "page_url": page_url,
                    "image_url": img.get_attribute("src"),
                }
            )
        finally:
            page.close() if page else None

        return page_fail_results, fail

    def _check_image(self, img_element: Locator, page_url: str) -> (int, int):
        try:
            img_url = img_element.get_attribute("src", timeout=0)

            box = img_element.bounding_box()
            if not box:
                logger.error(
                    f"No bounding box, element is not visible",
                    extra={
                        "page_url": page_url,
                        "img_url": img_url,
                        "reason": "No bounding box",
                    },
                )
                return

            dimensions = img_element.evaluate("""
                (img) => {
                    return {
                        width: img.width,
                        height: img.height,
                        naturalWidth: img.naturalWidth,
                        naturalHeight: img.naturalHeight,
                    };
                }
            """)

            width = dimensions.get("width")
            height = dimensions.get("height")

            n_width = dimensions.get("naturalWidth")
            n_height = dimensions.get("naturalHeight")

            if (width == 0 or height == 0) or (n_width == 0 or n_height == 0):
                logger.error(
                    f"Image failed to load (size 0)",
                    extra={
                        "page_url": page_url,
                        "img_url": img_url,
                        "reason": "Image failed to load (size 0)",
                    },
                )
                raise Exception("Image failed to load (size 0)")

            if width is None or height is None:
                logger.error(
                    f"Image failed to load (size None)",
                    extra={
                        "page_url": page_url,
                        "img_url": img_url,
                        "reason": "Image failed to load (size None)",
                    },
                )
                raise Exception("Image failed to load (size None)")

            w = width or n_width
            h = height or n_height

            return w, h

        except Exception as e:
            raise e
