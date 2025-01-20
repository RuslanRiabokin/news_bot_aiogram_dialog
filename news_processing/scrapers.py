import asyncio
import logging
from typing import List, Optional, Callable
import requests
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright, Page


class WebScraper:
    @staticmethod
    def scrape_static_page(url: str,
                           headers: Optional[dict] = None,
                           selector: str = 'body',
                           parser: str = 'html.parser',
                           extract_method: Callable = lambda soup: soup.get_text(),
                           timeout: int = 30) -> str:
        """
        Scrape content from a static web page.

        :param url: URL of the page to scrape
        :param headers: Optional headers for the request
        :param selector: CSS selector to target specific elements
        :param parser: BeautifulSoup parser to use
        :param extract_method: Function to extract content from BeautifulSoup object
        :param timeout: Request timeout in seconds
        :return: Extracted content as string
        """
        try:
            logging.info(f'Scraping static site: {url}')
            response = requests.get(url, headers=headers, timeout=timeout)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, parser)
            content = extract_method(soup.select_one(selector))
            return content.strip() if isinstance(content, str) else content
        except Exception as e:
            logging.error(f"Error scraping {url}: {str(e)}")
            return ""

    @staticmethod
    async def scrape_dynamic_page(url: str,
                                  timeout: int = 30000,
                                  wait_until: str = "networkidle",
                                  scroll: bool = True,
                                  scroll_behavior: str = "auto",
                                  wait_for_selector: Optional[str] = None,
                                  close_popups: bool = True,
                                  popup_selectors: List[str] = ['button:has-text("Close")', '[aria-label="Close"]'],
                                  content_selectors: List[str] = ['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'article',
                                                                  'section', 'div'],
                                  headless: bool = True,
                                  proxy: Optional[dict] = None) -> str:
        """
        Scrape content from a dynamic web page using Playwright.

        :param url: URL of the page to scrape
        :param timeout: Navigation timeout in milliseconds
        :param wait_until: Navigation wait until condition
        :param scroll: Whether to scroll the page
        :param scroll_behavior: Scrolling behavior ('auto', 'smooth')
        :param wait_for_selector: Optional selector to wait for before scraping
        :param close_popups: Whether to attempt closing popups
        :param popup_selectors: List of selectors for popup close buttons
        :param content_selectors: List of selectors for content extraction
        :param headless: Whether to run browser in headless mode
        :param proxy: Optional proxy configuration
        :return: Extracted content as string
        """
        async with async_playwright() as p:
            logging.info(f'Scraping dynamic site: {url}')
            browser = await p.chromium.launch(headless=headless)
            context = await browser.new_context(proxy=proxy) if proxy else await browser.new_context()
            page = await context.new_page()

            try:
                page.on("dialog", lambda dialog: asyncio.create_task(dialog.dismiss()))
                await page.goto(url, timeout=timeout, wait_until=wait_until)

                if wait_for_selector:
                    await page.wait_for_selector(wait_for_selector, state="visible", timeout=timeout)

                if scroll:
                    await WebScraper._scroll_page(page, scroll_behavior)

                if close_popups:
                    await WebScraper._close_popups(page, popup_selectors)

                text_content = await page.evaluate(WebScraper._extract_content_js(content_selectors))
                return text_content.strip()
            except Exception as e:
                logging.error(f"Error scraping {url}: {str(e)}")
                return ""
            finally:
                await browser.close()

    @staticmethod
    async def _scroll_page(page: Page, behavior: str = "auto"):
        await page.evaluate(f"window.scrollTo(0, document.body.scrollHeight, {{ behavior: '{behavior}' }});")
        await page.wait_for_timeout(2000)

    @staticmethod
    async def _close_popups(page: Page, selectors: List[str]):
        for selector in selectors:
            try:
                await page.click(selector, timeout=3000)
                logging.info(f"Closed popup using selector: {selector}")
            except:
                logging.debug(f"No popup found for selector: {selector}")

    @staticmethod
    def _extract_content_js(selectors: List[str]) -> str:
        return f"""
        () => {{
            const elements = document.querySelectorAll('{", ".join(selectors)}');
            return Array.from(elements)
                .map(el => el.innerText)
                .filter(text => text.trim().length > 0)
                .join(' ');
        }}
        """


# Usage example
async def main():
    scraper = WebScraper()
    static_content = scraper.scrape_static_page("https://example.com",
                                                selector='body',
                                                extract_method=lambda soup: soup.find_all('p'))
    print("Static content:", static_content)

    dynamic_content = await scraper.scrape_dynamic_page("https://example.com",
                                                        scroll=True,
                                                        wait_for_selector='body',
                                                        content_selectors=['p', 'h1', 'article'])
    print("Dynamic content:", dynamic_content)


if __name__ == "__main__":
    asyncio.run(main())