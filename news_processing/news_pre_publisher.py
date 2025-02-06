from __future__ import annotations

import asyncio
import html
import logging
from datetime import datetime, timedelta

from db_layer.db_factory import get_data_serice
from news_processing.news_API import BingNewsAPI
from news_processing.news_image_processing import main as get_image_news
from news_processing.news_publisher import publish_news_standart, publish_news_one_picture, publish_news_digest

get_news = BingNewsAPI()


async def is_time_to_publish(last_published_time, publish_frequency, status, news_id, db):
    """
    Перевіряє, чи можна публікувати новину на основі часу її публікації.
    """
    try:
        pub_dates = await db.get_publish_date(news_id)
        pub_times = await db.get_publish_time(news_id)
        now = datetime.now()
        last_pub_time = datetime.strptime(last_published_time, "%Y-%m-%d %H:%M:%S")

        if not pub_dates and not pub_times:
            return False

        if status != 'yes':
            return False

        is_time = False  # Стандартно ініціалізуємо як False

        for pub_date in pub_dates:
            for pub_time in pub_times:
                sended = await db.get_sended_status(news_id, pub_time[0])

                # Перевірка на "щодня"
                if pub_date[0] == 'everyday':
                    if pub_time[0] == 'every--hour':
                        is_time = now - last_pub_time >= timedelta(hours=1)
                    elif pub_time[0] == 'every-2-hour':
                        is_time = now - last_pub_time >= timedelta(hours=2)
                    elif pub_time[0] == 'every-3-hour':
                        is_time = now - last_pub_time >= timedelta(hours=3)
                    else:
                        if sended[0] == 0:
                            hour, minute = map(int, pub_time[0].split(':'))
                            target_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
                            is_time = now >= target_time
                            if is_time:
                                await db.set_sended_status_true(news_id, pub_time[0])
                # Перевірка на конкретну дату
                else:
                    pub_date_obj = datetime.strptime(pub_date[0], "%Y-%m-%d").date()
                    if pub_date_obj <= now.date():
                        if pub_time[0] == 'every--hour':
                            is_time = now - last_pub_time >= timedelta(hours=1)
                        elif pub_time[0] == 'every-2-hour':
                            is_time = now - last_pub_time >= timedelta(hours=2)
                        elif pub_time[0] == 'every-3-hour':
                            is_time = now - last_pub_time >= timedelta(hours=3)
                        else:
                            if sended[0] == 0:
                                hour, minute = map(int, pub_time[0].split(':'))
                                target_time = datetime.combine(now.date(), datetime.min.time()).replace(
                                    hour=hour, minute=minute, second=0, microsecond=0
                                )
                                is_time = now >= target_time
                                if is_time:
                                    await db.set_sended_status_true(news_id, pub_time[0])

                # Якщо час публікації настав, виходимо з циклів
                if is_time:
                    break
            if is_time:
                break

        return is_time

    except Exception as e:
        print(f"Помилка під час перевірки часу публікації (ID {news_id}): {e}")
        return False
    # number = int(publish_frequency.rstrip('hm'))
    # print("перевірка новин на публікацію")
    # timestamp = time.time()
    # dt_from_timestamp = datetime.fromtimestamp(timestamp)
    # dt_from_string = datetime.strptime(last_published_time, "%Y-%m-%d %H:%M:%S")
    # time_difference = dt_from_timestamp - dt_from_string
    # hours_difference = time_difference.total_seconds() / 3600
    # is_time = hours_difference > int(number)
    # is_time_to_delete = hours_difference > 24
    #
    # if status == 'no' and is_time_to_delete:
    #     await db.delete_deactivated_news(news_id)
    # return is_time


async def time_check(bot):
    # Підключаємося до бази даних
    async with get_data_serice() as db:

        # Отримуємо всі записи, що відповідають умовам публікації
        data = await db.get_channels_for_publishing()

        # Створюємо словник для digest новин за користувачами та каналами
        digest_topics_by_user_and_channel = {}

        # Обробляємо кожен запис
        for item in data:
            topic_id = item['id']
            topic = item['topic_name']  # Тема новини
            topic = html.escape(topic)
            channel = item['channel_name']  # Канал для публікації
            user_id = item['user_id']  # ID користувача
            publish_frequency = item['publish_frequency']  # Частота публікацій
            news_type = item['news_type']  # Тип новини (standart, picture, digest)
            last_pub_time = item['last_pub_time']  # Час останньої публікації
            poll = item['add_poll']  # yes | no
            poll_text = item['poll_text']
            status = item['is_active']

            # Перевіряємо, чи час публікації відповідає частоті публікації
            is_time = await is_time_to_publish(last_pub_time, publish_frequency, status, news_id=topic_id, db=db)

            if is_time and status == 'yes':
                # Якщо тип новини - standart, викликаємо функцію publish_standart_news
                if news_type == 'standart':
                    await publish_standart_news(db, bot, topic=topic, channel=channel, poll=poll,
                                                poll_text=poll_text, user_id=user_id, topic_id=topic_id)

                # Якщо тип новини - picture, викликаємо функцію publish_picture_news
                elif news_type == 'picture':
                    await publish_picture_news(bot, topic=topic, channel=channel, poll=poll,
                                               poll_text=poll_text, user_id=user_id, topic_id=topic_id, db=db)

                # Якщо тип новини - digest
                elif news_type == 'digest':
                    # Групуємо digest новини за користувачем і каналом
                    if user_id not in digest_topics_by_user_and_channel:
                        digest_topics_by_user_and_channel[user_id] = {}

                    if channel not in digest_topics_by_user_and_channel[user_id]:
                        digest_topics_by_user_and_channel[user_id][channel] = {
                            'id': [],
                            'topics': []
                        }

                    digest_topics_by_user_and_channel[user_id][channel]['topics'].append(topic)
                    digest_topics_by_user_and_channel[user_id][channel]['id'].append(topic_id)

        # Після проходження по всіх записах перевіряємо digest новини
        for user_id, channels_data in digest_topics_by_user_and_channel.items():
            for channel, data in channels_data.items():
                topics = data['topics']
                topic_id = data['id']

                # Якщо є новини для публікації, викликаємо publish_digest_news
                if len(topics) >= 2:
                    await publish_digest_news(bot, topics=topics, channel=channel, poll=poll,
                                              poll_text=poll_text, user_id=user_id, topics_id=topic_id)
                else:
                    # Якщо менше двох тем для публікації, публікуємо як picture
                    topics = topics[0]
                    await publish_picture_news(bot, topics, channel=channel, poll=poll,
                                               poll_text=poll_text, user_id=user_id, topic_id=topic_id[0], db=db)


async def publish_standart_news(db, bot, topic: str, channel: str, poll: str, poll_text: str,
                                user_id: str, topic_id: str) -> None:
    try:
        print('try to publish standart news')
        channel_url = channel
        responses = await get_news.main(request=topic, channel=channel, search_type='standart')
        themes_dict: dict = {'themes': responses}
        topic_text = themes_dict['themes'][topic].get('general_text')
        topic_url = themes_dict['themes'][topic].get('url')
        topic_url = f' <a href="{topic_url}"><b> Джерело </b></a>'

        await asyncio.gather(
            publish_news_standart(bot, channel_url, topic_text, topic_url, topic, poll=poll, poll_text=poll_text,
                                  user_id=user_id),
            db.update_last_published_time(topic_id=topic_id)
        )
    except Exception as e:
        logging.exception('Publish_news Exception in publish_standart_news', exc_info=e)


async def publish_picture_news(bot, topic: str, channel: str, poll: str, poll_text: str,
                               user_id: str, topic_id: str, db: get_data_serice) -> None:
    try:
        news_path, topic_url = await get_image_news(topic=topic, channel=channel)

        # Створення паралельних задач
        publish_task = asyncio.create_task(
            publish_news_one_picture(bot, channel_id=channel, news_path=news_path,
                                     source=topic_url, topic=topic, poll=poll, poll_text=poll_text, user_id=user_id))
        db_task = asyncio.create_task(db.update_last_published_time(topic_id=topic_id))

        # Очікування завершення публікації новин
        await publish_task
        await asyncio.sleep(1)  # Можеш видалити це, якщо нема потреби в затримці
        # Очікування завершення оновлення бази даних
        await db_task


    except Exception as e:
        logging.exception('Publish_news Exception in publish_picture_news', exc_info=e)
        pass


async def publish_digest_news(bot, channel: str, topics: list[str], poll: str, poll_text: str,
                              user_id: str, topics_id: list) -> None:
    async with get_data_serice() as db:
        try:
            path_links = {}

            # Отримуємо новини для кожної теми
            for topic in topics:
                try:
                    news_path, topic_url = await get_image_news(topic=topic, channel=channel)
                    path_links[topic] = [news_path, topic_url]
                except Exception as e:
                    logging.exception(f"Error during getting news for topic {topic}:", exc_info=e)
                    continue

            # Публікуємо всі новини разом в один канал
            if path_links:
                if channel:
                    try:
                        # Викликаємо функцію публікації
                        await publish_news_digest(bot, channel_id=channel, data=path_links, topics=topics,
                                                  poll=poll, poll_text=poll_text, user_id=user_id)

                        # Оновлюємо час публікації тільки для справжніх тем
                        for topic in topics:
                            try:
                                for topic_id in topics_id:
                                    await db.update_last_published_time(topic_id=topic_id)
                            except Exception as e:
                                logging.exception(f"Error updating last published time for {topic}", exc_info=e)
                                continue
                    except Exception as e:
                        logging.exception("Error during publishing news digest", exc_info=e)
                else:
                    logging.warning("Channel not found for publication.")
            else:
                logging.warning("No valid news to publish in digest.")
        except Exception as e:
            logging.exception('Publish_news Exception', exc_info=e)
