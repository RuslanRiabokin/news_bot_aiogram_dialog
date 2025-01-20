import asyncio
import hashlib
import logging
import aiohttp

from datetime import datetime
from urllib.parse import urlencode
from langdetect import detect

from config import BG_KEY_1, BG_KEY_2, BG_ENDPOINT, BGS_KEY_1, BGS_KEY_2, BGS_ENDPOINT
from news_processing.processing_API import WebScraperTranslator
from news_processing.ttl_cache_class import TTLCache

wst = WebScraperTranslator()


class BingNewsAPI:
    def __init__(self):
        self.categories = [
                            "australia", "business", "entertainment", "politics", "sports", "world",
                            "canada", "business", "canada", "entertainment", "lifestyle",
                            "politics", "scienceandtechnology", "sports", "world",
                            "china", "auto", "business", "china", "education",
                            "entertainment", "military", "realestate", "science and technology",
                            "society", "sports", "world",
                            "india", "business", "entertainment", "india", "lifestyle",
                            "politics", "scienceandtechnology", "sports", "world",
                            "japan", "business", "entertainment", "japan", "lifestyle",
                            "politics", "scienceandtechnology", "sports", "world",
                            "united kingdom", "business", "entertainment", "health",
                            "politics", "scienceandtechnology", "sports", "uk", "world",
                            "united states", "business", "entertainment",
                            "entertainment movieandtv", "entertainment music", "health",
                            "politics", "products", "science and technology", "technology", "science",
                            "sports", "sports golf", "sports mlb", "sports nba", "sports nfl",
                            "sports nhl", "sports soccer", "sports tennis", "sports cfb",
                            "sports cbb", "us", "us northeast", "us south", "us midwest",
                            "us west", "world", "world africa", "world americas", "world asia",
                            "world europe", "world middleeast"
                        ]
        self.language_region_map = {
    'en': 'US', 'ru': 'RU', 'uk': 'UA', 'de': 'DE', 'fr': 'FR', 'es': 'ES', 'it': 'IT', 'pt': 'PT', 'ja': 'JP', 'ko': 'KR',
    'zh': 'CN', 'ar': 'SA', 'hi': 'IN', 'bn': 'BD', 'tr': 'TR', 'pl': 'PL', 'nl': 'NL', 'sv': 'SE', 'no': 'NO', 'da': 'DK',
    'fi': 'FI', 'cs': 'CZ', 'ro': 'RO', 'el': 'GR', 'hu': 'HU', 'he': 'IL', 'th': 'TH', 'vi': 'VN', 'id': 'ID', 'ms': 'MY',
    'sr': 'RS', 'hr': 'HR', 'sk': 'SK', 'bg': 'UA', 'sq': 'AL', 'ca': 'ES', 'eu': 'ES', 'kk': 'KZ', 'tk': 'TM',
    'uz': 'UZ', 'ky': 'KG', 'tt': 'RU', 'be': 'BY', 'hy': 'AM', 'az': 'AZ', 'is': 'IS', 'at': 'AT', 'ch': 'CH',
    'cz': 'CZ', 'lv': 'LV', 'lt': 'LT', 'mt': 'MT', 'rs': 'RS', 'mk': 'MK', 'cy': 'CY',
    'lu': 'LU', 'ba': 'BA', 'me': 'ME', 'al': 'AL', 'ee': 'EE', 'se': 'SE', 'dk': 'DK',
}

        self.ttl_cache = TTLCache(ttl=3600 * 12)

    async def get_url_hash(self, url: str) -> str:
        return hashlib.sha256(url.encode()).hexdigest()

    def parse_bing_date(self, date_str):
        if '.' in date_str:
            date_str = date_str[:date_str.index('.') + 7] + 'Z'
        return datetime.strptime(date_str, '%Y-%m-%dT%H:%M:%S.%fZ')

    def sort_news_by_date(self, news_list):
        return sorted(news_list, key=lambda x: self.parse_bing_date(x['datePublished']), reverse=True)

    async def get_news_from_bing(self, query_list: list, channel_id: str, search_type: str) -> list or None:
        results = []
        for query in query_list:
            if query in self.categories:
                search_type = 'news'

        try:
            async with aiohttp.ClientSession() as session:
                tasks = []
                for query in query_list:
                    params = self._get_params(query, search_type)
                    endpoint, key_1, key_2 = self._get_endpoint_and_keys(search_type)

                    query_string = urlencode(params)
                    url = f'{endpoint}?{query_string}'

                    headers = {'Ocp-Apim-Subscription-Key': key_1}
                    headers_reserve = {'Ocp-Apim-Subscription-Key': key_2}

                    tasks.append(self.fetch_bing_data(session, url, headers, headers_reserve, query, search_type))

                responses = await asyncio.gather(*tasks)

                results = self._process_responses(responses, query_list, search_type)

                sorted_results = self.sort_news_by_date(results)
                return sorted_results if sorted_results else None
        except Exception as ex:
            logging.exception('Exception in get_news_from_bing', exc_info=ex)
            return None

    def get_request_language(self, query: str) -> str:
        unique_chars = {
        'uk': 'єіїґ',
        'ru': 'ёыэъ',
        'be': 'ўэ',
        'de': 'äöüß'
    }
        for lang, chars in unique_chars.items():
            if any(char in query for char in chars):
                return lang

        try:
            request_lang = detect(query)
            return request_lang if request_lang in unique_chars else 'en'
        except Exception:
            return 'en'
        

    def _get_params(self, query, search_type):
        language = self.get_request_language(query)
        region = self.language_region_map.get(language, 'US')
        print(f'{language} - {region}')

        params = {'q': query,'cc': region ,'setLang': language, 'originalImg': True}

        if search_type == 'news':
            params['freshness'] = 'week'
        elif search_type == 'standart':
            params['answerCount'] = '2'
            params['promote'] = 'News,Webpages'
            params['q'] += '" news"'

        return params

    def _get_endpoint_and_keys(self, search_type):
        if search_type == 'news':
            return BG_ENDPOINT, BG_KEY_1, BG_KEY_2
        else:
            return BGS_ENDPOINT, BGS_KEY_1, BGS_KEY_2

    async def fetch_bing_data(self, session, url, headers, headers_reserve, category, search_type) -> dict:
        try:
            async with session.get(url, headers=headers) as response:
                data = await response.json()
                if data:
                    data['category'] = category
                return data
        except Exception as ex:
            logging.exception("Error fetch_bing_data", exc_info=ex)
            async with session.get(url, headers=headers_reserve) as response:
                data = await response.json()
                if data:
                    data['category'] = category
                return data

    def _process_responses(self, responses, query_list, search_type):
        results = []
        for idx, data in enumerate(responses):
            if data:
                if search_type == 'news':
                    results.extend(self._process_news_results(data, query_list[idx]))
                else:
                    results.extend(self._process_standard_results(data, query_list[idx]))
        return results

    def _process_news_results(self, data, category):
        return [{
            'url': item.get('url'),
            'general_text': item.get('description', ''),
            'categories': data.get('category', category),
            'image_url': item.get('image', {}).get('thumbnail', {}).get('contentUrl') if item.get('image') else 'None',
            'datePublished': item.get('datePublished')
        } for item in data.get('value', [])]

    def _process_standard_results(self, data, category):
        results = []
        for item in data.get('webPages', {}).get('value', []):
            results.append({
                'url': item.get('url'),
                'general_text': item.get('snippet', ''),
                'categories': category,
                'image_url': 'None',
                'datePublished': item.get('datePublished') or item.get('dateLastCrawled')
            })
        for item in data.get('news', {}).get('value', []):
            results.append({
                'url': item.get('url'),
                'general_text': item.get('description', ''),
                'categories': category,
                'image_url': item.get('image', {}).get('thumbnail', {}).get('contentUrl') if item.get(
                    'image') else 'None',
                'datePublished': item.get('datePublished')
            })
        return results

    async def main(self, request, channel=None, search_type='news') -> dict or None:
        if isinstance(request, str):
            request = [request]
        request = list(set(request))  # Унікальні запити
        news = {}
        news_list = await self.get_news_from_bing(query_list=request, channel_id=channel, search_type=search_type)
        # print('News list = {}'.format(news_list), '\n'*4)

        if news_list:
            try:
                for item in news_list:
                    category = item.get('categories')
                    url = item.get('url')
                    url_hash = await self.get_url_hash(url)

                    await self.ttl_cache.clean_up()

                    if not self.ttl_cache.contains(url_hash, channel):
                        self.ttl_cache.add(url_hash, channel)
                        general_text = item.get('general_text', '')
                        # print('General text: {}'.format(general_text), '\n'*4)
                        check_for_article = await wst.check_article(content=general_text, url=url)
                        # print('Check from article', type(check_for_article), '\n'*4)
                        if check_for_article == 'True':
                            # print(bool(check_for_article))
                            translated_text = await wst.translate_string(content=general_text, url=url, raw_text=item)
                            item['general_text'] = translated_text
                            news[category] = item
                            break  # Вибираємо першу непубліковану новину
                        else:
                            # Потрібно вибрати другу статтю з повернених
                            continue

                if not news:
                    # Якщо всі новини вже опубліковані, вибираємо найновішу
                    latest_news = news_list[0]
                    category = latest_news.get('categories')
                    url = latest_news.get('url')
                    general_text = latest_news.get('general_text', '')
                    translated_text = await wst.translate_string(content=general_text, url=url)
                    latest_news['general_text'] = translated_text
                    news[category] = latest_news

            except Exception as ex:
                logging.exception('Error in main in news_API', exc_info=ex)

            return news
        else:
            return await self._get_cat_image(request[0])

    async def _get_cat_image(self, category):
        url = 'https://api.thecatapi.com/v1/images/search'
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                data = await response.json()
                return {category: {
                    'url': data[0].get('url'),
                    'general_text': f'Згідно з вашим запитом {category} наразі нічого не знайдено.\n Ось Вам котик:',
                    'categories': category,
                    'image_url': data[0].get('url'),
                }}


# Приклад використання
if __name__ == "__main__":
    bing_api = BingNewsAPI()
    req_list = ['Спорт в Україні',]
    for item in req_list:
        result = asyncio.run(bing_api.main(request=item, search_type='standart'))
        print(result)
