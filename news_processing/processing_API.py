import asyncio
import logging
import os

import requests
from deep_translator import GoogleTranslator
from dotenv import load_dotenv
from openai import AzureOpenAI

from news_processing.scrapers import WebScraper as ws


class WebScraperTranslator:
    def __init__(self):
        load_dotenv()
        self.client = AzureOpenAI(
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            api_version="2024-02-01",
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
        )

    @staticmethod
    def is_dynamic_site(url):
        response = requests.get(url, timeout=5)
        return len(response.text) < 1000 or "<script" in response.text.lower()

    async def translate_string(self, content, url, from_lang='auto', to_lang='uk', raw_text=None):
        content_str = str(content)

        try:
            check_site = self.is_dynamic_site(url)
            text = await ws.scrape_dynamic_page(url) if check_site else ws.scrape_static_page(url)
        except Exception as e:
            logging.exception('Cannot scrape site', exc_info=e)
            text = content_str

        text = text if text else content_str
        if len(text) > 120000:
            text = text[:120000]
        if raw_text and len(raw_text) < 1000:
            text = raw_text

        try:
            response = self.client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": (
                            f'Focus on extracting content closely related to the topic in "content_str". '
                            f'Remove any administrative messages, privacy notices, or unrelated information. '
                            f'If the related content is insufficient or unavailable, keep "content_str" as is without modification. '
                            f'Ensure the result is not more than 450 characters and structured as follows: '
                            f'start with the article title, followed by two line breaks, and then a summary. '
                            f'Translate the result to {to_lang} and add expressiveness using emojis.'
                        )
                    },
                    {"role": "user", "content": f'Content to work with: "{text} and {content_str}". Max return text length is 450 characters.'}
                ],
                model="talex-mode",
            )
            return response.choices[0].message.content
        except Exception as e:
            logging.exception("Translation failed with OpenAI API error", exc_info=e)
            try:
                translated_text = GoogleTranslator(target=to_lang).translate(content_str)
                return translated_text
            except Exception as e:
                logging.exception("Google Translate also failed", exc_info=e)
                return content_str

    async def check_article(self, content, url=None):
        text = content

        if len(text) > 120000:
            text = text[:120000]

        try:
            response = self.client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": (
                            'Your task is to analyze the provided text and classify it into one of two categories: '
                            '"News Article" or "News Promotion/Advertisement". '
                            'If the text seems like a full news article (with actual information, context, or events), '
                            'return True. '
                            'If the text looks like a promotion, a brief summary, or an advertisement (e.g., encouraging people '
                            'to read news on a website or app), return False.'
                        )
                    },
                    {"role": "user", "content": f'Content to analyze: "{text}"'}
                ],
                model="talex-mode",
            )
            return response.choices[0].message.content

        except Exception as e:
            logging.exception("Translation failed with OpenAI API error", exc_info=e)


# Usage example
async def main():
    scraper_translator = WebScraperTranslator()
    url = "https://example.com"
    content = "Example content"
    result = await scraper_translator.translate_string(content, url)
    print(result)

if __name__ == "__main__":
    asyncio.run(main())