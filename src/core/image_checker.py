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
            cdp_session = page.context.new_cdp_session(page)
            cdp_session.send("Network.setCacheDisabled", {"cacheDisabled": True})

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

            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            page.wait_for_timeout(1000)

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
            img_element.scroll_into_view_if_needed()
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
                async (img) => {
                    const delay = (ms) => new Promise(resolve => setTimeout(resolve, ms));

                    const checkDimensions = (el) => {
                        const isSvg = el.currentSrc.toLowerCase().endsWith('.svg') || el.src.startsWith('data:image/svg+xml');
                        const hasPixels = el.naturalWidth > 0 || (isSvg && el.getBoundingClientRect().width > 0);
                        
                        return {
                            naturalWidth: el.naturalWidth,
                            naturalHeight: el.naturalHeight,
                            hasPixels: hasPixels,
                            complete: el.complete,
                            src: el.currentSrc || el.src
                        };
                    };

                    let res = checkDimensions(img);
                    if (!img.complete) {
                        await new Promise(r => { img.onload = r; img.onerror = r; setTimeout(r, 5000); });
                    }

                    res = checkDimensions(img);
                    if (!res.hasPixels && img.complete) {
                        await delay(300); 
                        res = checkDimensions(img);
                    }

                    return res;
                }
            """)

            n_width = dimensions.get("naturalWidth")
            n_height = dimensions.get("naturalHeight")
            complete = dimensions.get("complete")

            if not complete:
                logger.error(
                    f"Image failed to load (complete False)",
                    extra={
                        "page_url": page_url,
                        "img_url": img_url,
                        "reason": "Image failed to load (complete False)",
                    },
                )
                raise Exception("Image failed to load (complete False)")

            if n_width == 0 and n_height == 0:
                logger.error(
                    f"Image failed to load (size 0)",
                    extra={
                        "page_url": page_url,
                        "img_url": img_url,
                        "naturalWidth": n_width,
                        "naturalHeight": n_height,
                        "complete": complete,
                        "reason": "Image failed to load (size 0)",
                    },
                )
                raise Exception("Image failed to load (size 0)")

            return n_width, n_height

        except Exception as e:
            raise e
