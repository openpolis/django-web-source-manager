import re
import time
from typing import Optional
from bs4 import BeautifulSoup
from playwright.sync_api import Browser
from playwright.sync_api import sync_playwright, Error as PlaywrightError, Playwright
from ..conf import *
from urllib.parse import urljoin
import logging

class PlaywrightWrapper:
    """Pooled playwright (https://playwright.dev) wrapper, that allows users to
    get live textual content and status from URLs, and selectors

    simple usage:

        p = PlaywrightWrapper(request_ua=REQUEST_UA)
        status, content = p.get_live_content(url, selector)

    Resources (Playwright instance, Browser, Context and Page are pooled.
    This drastically reduces the time it takes, avoiding the need to create Browser and/or Pages anew.
    """
    p: Playwright
    browser: Browser
    proxy: Optional[dict]
    request_timeout: int
    request_ua: str

    def __init__(
            self,
            use_proxy: bool = False,
            proxy: Optional[dict] = None,
            request_ua: str = REQUESTS_UA,
            request_timeout_sec: int = REQUESTS_MAX_TIMEOUT,
            browser_set: Optional[str] = 'chrome',
            logger: Optional[logging.Logger] = None
    ):
        if not logger:
            self.logger = logging.getLogger(f"project.{__name__}")
            self.logger.setLevel(logging.INFO)
        self.p = sync_playwright().start()
        self.use_proxy = use_proxy
        # if proxy was not passed among the arguments,
        # then check if it's in the settings
        self.proxy = proxy
        if self.use_proxy and proxy:
            self.proxy = proxy
        if self.use_proxy and proxy is None and PROXY_URL:
            self.proxy = {
                'url': PROXY_URL,
                'username': PROXY_USERNAME,
                'password': PROXY_PASSWORD
            }

        self.request_ua = request_ua
        self.request_timeout = request_timeout_sec * 1000
        if browser_set == 'chrome':
            self.browser = self.p.chromium.launch(**self.get_browser_args())
        elif browser_set == 'firefox':
            self.browser = self.p.firefox.launch(**self.get_browser_args())
        self.context = self.browser.new_context(**self.get_browser_context_args())
        self.page = self.context.new_page()

    def get_browser_args(self):
        """Prepare browser args."""
        browser_args = {"headless": True, "args": ["--disable-http2"]}

        proxy_configured = (
                self.proxy and 'url' in self.proxy and 'username' in self.proxy and 'password' in self.proxy
        )

        if proxy_configured:
            browser_args.update(
                {
                    "proxy": {
                        "server": self.proxy['url'],
                        "username": self.proxy['username'],
                        "password": self.proxy['password'],
                    }
                }
            )
        return browser_args

    def get_browser_context_args(self):
        """Prepare browser context args."""
        browser_args = {"ignore_https_errors": True}
        if self.request_ua:
            browser_args.update({"user_agent": self.request_ua})
        return browser_args

    # @property
    # def browser_and_context(self):
    #     browser: Browser = self.p.chromium.launch(**self.get_browser_args())
    #     context = browser.new_context(**self.get_browser_context_args())
    #     return browser, context

    @staticmethod
    def convert_relative_links_to_absolute(html, base_url):
        soup = BeautifulSoup(html, 'html.parser')
        for tag in soup.find_all('a', href=True):
            tag['href'] = urljoin(base_url, tag['href'])
            tag['target'] = '_blank'
        return str(soup)

    def by_pass_with_google(self, url):
        self.page.goto(
            f'https://www.google.it/search?q={url}',
            wait_until="load", timeout=self.request_timeout)
        self.page.query_selector_all('button')[-3].click()
        with self.page.expect_navigation() as response_info:
            self.page.query_selector_all('h3')[0].click()

        response = response_info.value
        return response

    def get_live_content(self, url, selector, output_format, **kwargs):
        """
        Requests content from URI, using playwright (https://playwright.dev/python/)

        Finds the content using the object's selector attribute
        (an XPATH or a CSS or some other _locators_, as specified in https://playwright.dev/python/docs/locators).

        :return: 2-tuple
          the cleanest possible textual content, or a comprehensible error message,
          along with the response status code
        """
        selector = selector or "body"
        time_response_took = None

        try:
            time_response_start = time.time()
            response = self.page.goto(url, wait_until="load", timeout=self.request_timeout)
            time_response_took = time.time() - time_response_start
        except PlaywrightError as e:
            status = 990
            content = str(e)
        else:
            status = response.status
            if status in (200, 202):
                regex = r"(?:\n|\t|\xa0)+(?:\s+(?:\n|\t|\xa0)+)?"
                locator = self.page.locator(selector)

                try:
                    count = locator.count()
                except PlaywrightError as e:
                    status = 900
                    content = f"{e}"
                else:
                    if not count:
                        status = 900
                        content = "Selettore non trovato"

                    elif count > 1:
                        if output_format == 'text':
                            content = locator.all_inner_texts()
                            content = "\n".join(
                                re.sub(regex, "\n", x.strip("- \n\t")) for x in content
                            )
                        elif output_format == 'html':
                            base_url = url
                            elements_html = [self.convert_relative_links_to_absolute(element.inner_html(), base_url) for
                                             element in locator.element_handles()]

                            content = ' '.join(elements_html)
                    else:
                        if output_format == 'text':
                            content = locator.inner_text()
                            content = re.sub(regex, "\n", content.strip("- \n\t"))
                        elif output_format == 'html':
                            inner_html = locator.inner_html()
                            base_url = url
                            html_with_absolute_links = self.convert_relative_links_to_absolute(inner_html, base_url)
                            content = html_with_absolute_links

                        else:
                            raise Exception("Invalid output format")


            else:
                if status == 404:
                    content = "Pagina non trovata"
                else:
                    content = response.status_text

        if time_response_took:
            trt = f"{time_response_took:.03}s"
        else:
            trt = f"-"

        if status in [200, 202]:
            error_msg = "-"
        else:
            error_msg = content

        self.logger.debug(f"{url} - {selector} - {status} - {error_msg} - {trt}")

        return status, content

    def stop(self):
        self.page.close()
        self.browser.close()
        self.p.stop()
