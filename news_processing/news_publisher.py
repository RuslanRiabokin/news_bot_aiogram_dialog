# news_publisher.py
# Файл реализует логику публикации новостей в Telegram-каналы.
# Включает проверку каналов для публикации и учет частоты публикаций (раз в час).
from __future__ import annotations

import logging
from aiogram import types
from aiogram.types import FSInputFile

from db_layer.database import AsyncDatabase  # Імпорт класу роботи з базою даних


async def publish_news_standart(bot, channel_id: str, news: str, source: str,
                                topic: str, poll: str, poll_text: str, user_id: str, news_type: str = "text"):
    """
    Публікує новину в заданий канал Telegram з посиланням на джерело.
    """
    try:
        topic_tag: str = topic.replace(" ", "_")
        message: types.Message = await bot.send_message(
            chat_id=channel_id,
            text=f"#{topic_tag}\n\n{news}\n\n{source}"
        )

        if poll == 'yes':
            await send_poll(bot, user_id, channel_id, message=message, poll_text=poll_text)
    except Exception as e:
        logging.exception(f"Не вдалося опублікувати новину в {channel_id}", exc_info=e)


async def publish_news_one_picture(bot, channel_id: str, news_path: str, user_id: str,
                                   source: str, topic: str, poll: str, poll_text: str, news_type: str = "image"):
    """
    Публікує фото-новину в заданий канал Telegram.
    """
    try:
        topic_tag: str = topic.replace(" ", "_")
        photo = FSInputFile(news_path)

        # Відправляємо фото
        message = await bot.send_photo(
            chat_id=channel_id,
            photo=photo,
            caption=f"#{topic_tag} {source}",
            show_caption_above_media=True,
        )

        if poll == 'yes':
            await send_poll(bot, user_id, channel_id, message=message, poll_text=poll_text)
    except Exception as e:
        logging.exception(f"Не вдалося опублікувати новину в {channel_id}", exc_info=e)


async def publish_news_digest(bot, channel_id: str, data: dict, topics: list,
                              poll: str, poll_text: str, user_id: str, news_type: str = "digest"):
    """
    Публікує дайджест новин у вигляді групи медіа-файлів.
    """
    try:
        media_digest = []
        for topic in topics:
            topic_tag: str = topic.replace(" ", "_")
            caption = f"#{topic_tag} {data[topic][1]}"
            media_digest.append(types.InputMediaPhoto(
                media=FSInputFile(data[topic][0]),
                caption=caption,
                show_caption_above_media=True,
            ))

        # Відправляємо групу медіа
        await bot.send_media_group(chat_id=channel_id, media=media_digest)

        if poll == 'yes':
            await send_poll(bot, user_id, channel_id, message=None, poll_text=poll_text)
    except Exception as e:
        logging.exception(f"Не вдалося опублікувати новину в {channel_id}", exc_info=e)


async def send_poll(bot, user_id, channel_id, poll_text, message: types.Message | None):
    """
    Функція для створення та виправляння опитування.
    """
    poll_list = poll_text.split(',')
    poll_list = [item.strip() for item in poll_list]

    # Валідація: опитування повинно містити питання і як мінімум дві відповіді
    if len(poll_list) < 3:
        await bot.send_message(chat_id=user_id, text="Для опитування потрібно питання і хоча б дві відповіді.")
        raise ValueError("Для опитування потрібно питання і хоча б дві відповіді.")

    question = poll_list[0]
    answers = poll_list[1:]

    # Відправляємо опитування
    if message:
        await bot.send_poll(
            chat_id=channel_id,
            question=question,
            options=answers,
            reply_to_message_id=message.message_id  # Це робить опитування "відповіддю" на повідомлення
        )
    else:
        await bot.send_poll(
            chat_id=channel_id,
            question=question,
            options=answers
        )
