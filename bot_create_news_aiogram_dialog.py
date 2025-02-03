import logging
import operator
import re

from aiogram import Bot
from aiogram.enums import ChatMemberStatus
from aiogram.types import Message, CallbackQuery
from aiogram_dialog import Dialog, DialogManager, Window, ShowMode, StartMode
from aiogram_dialog.widgets.input import TextInput, ManagedTextInput
from aiogram_dialog.widgets.kbd import Button, Row, Column, Multiselect
from aiogram_dialog.widgets.text import Const, Format

from db_layer.db_factory import get_data_serice
from states_class_aiogram_dialog import MainDialogSG, SecondDialogSG


async def go_second_dialog(callback: CallbackQuery, button: Button, dialog_manager: DialogManager):
    """Перемикається на перше вікно другого діалогу"""
    await dialog_manager.start(state=SecondDialogSG.first)


async def switch_to_first_subscription(callback: CallbackQuery, button: Button, dialog_manager: DialogManager):
    """Перемикається на стан 'subscription' у першому діалозі"""
    await dialog_manager.switch_to(state=MainDialogSG.menu)


async def switch_to_first_lists(callback: CallbackQuery, button: Button, dialog_manager: DialogManager):
    """Перемикається на стан вибору тем у першому діалозі"""
    await dialog_manager.switch_to(state=MainDialogSG.new_subscription)


async def return_to_subscription(callback: CallbackQuery, button: Button, dialog_manager: DialogManager):
    """Повертається до стану 'subscription' у першому діалозі"""
    await dialog_manager.switch_to(state=MainDialogSG.menu)


async def get_topics(dialog_manager: DialogManager, **kwargs):
    """Повертає список тем для вибору в діалозі новин"""
    topics = [
        ("IT", '1'),
        ("Дизайн", '2'),
        ("Наука", '3'),
        ("Суспільство", '4'),
        ("Культура", '5'),
        ("Мистецтво", '6'),
    ]
    return {"topics": topics}


def news_check(text: str) -> str:
    """Перевірка тексту на наявність змісту і довжини"""
    stripped_text = text.strip()  # Прибираємо пробіли
    # Перевірка, що текст містить хоча б одну літеру та має правильну довжину
    if not stripped_text or not re.search(r'[a-zA-Zа-яА-Я]', stripped_text):
        raise ValueError("Введіть не порожнє повідомлення або текст, що містить літери.")
    if len(stripped_text) < 2:
        raise ValueError("Текст має бути не коротший за дві літери.")
    if len(stripped_text) > 25:
        raise ValueError("Текст не повинен перевищувати 25 символів.")
    return stripped_text



async def error_news_handler(
        message: Message,
        widget: ManagedTextInput,
        dialog_manager: DialogManager,
        error: ValueError):
    """Хендлер, який спрацює на ввід некоректної новини"""
    await message.answer(text=str(error))  # Виводимо повідомлення про помилку


async def correct_news_handler(message: Message, widget: ManagedTextInput, dialog_manager: DialogManager, text: str) -> None:
    """Обрабатывает корректно введённую новость и сохраняет её в базу данных."""
    await message.answer(text=f"Ви ввели новину: {text}")
    dialog_manager.dialog_data['selected_topics'] = [text]  # Сохраняем новость временно
    await dialog_manager.switch_to(state=MainDialogSG.channel_name, show_mode=ShowMode.SEND)




async def confirm_selected_topics(callback: CallbackQuery, button: Button, dialog_manager: DialogManager):
    """Підтверджує вибір новин і зберігає обрані теми в dialog_data для подальшого збереження в базу даних."""
    await callback.message.delete()

    # Отримуємо вибрані теми
    multi_topics_widget = dialog_manager.find("multi_topics")
    selected_topics = multi_topics_widget.get_checked()

    # Викликаємо get_topics, щоб отримати список всіх тем
    topics_data = await get_topics(dialog_manager)
    all_topics = topics_data["topics"]

    # Відбираємо назви тем за їх ідентифікаторами
    selected_topic_names = [name for name, id in all_topics if id in selected_topics]

    if selected_topic_names:
        topics_list = ", ".join(selected_topic_names)
        await callback.message.answer(f"Ви обрали наступні теми новин: {topics_list}", disable_notification=True)

        # Зберігаємо вибрані теми в dialog_data для подальшого збереження
        dialog_manager.dialog_data['selected_topics'] = selected_topic_names

        # Переходимо до введення каналу
        await dialog_manager.switch_to(state=MainDialogSG.channel_name, show_mode=ShowMode.SEND)
    else:
        await callback.message.answer("Ви не обрали жодної теми новин.", disable_notification=True)


async def handle_channel_name(
    message: Message, widget: ManagedTextInput, dialog_manager: DialogManager, text: str
) -> None:
    """Підтверджує назву каналу та зберігає дані підписки в базу даних."""
    bot: Bot = message.bot

    # Обробка каналу
    if text.startswith("https://t.me/"):
        channel_name = "@" + text.split("https://t.me/")[-1]
    elif not text.startswith("@"):
        channel_name = "@" + text
    else:
        channel_name = text

    try:
        # Проверяем статус бота в канале
        bot_chat_member = await bot.get_chat_member(channel_name, bot.id)

        # Проверяем статус пользователя в канале
        user_chat_member = await bot.get_chat_member(channel_name, message.from_user.id)

        # Проверяем, что бот и пользователь являются администраторами
        if (bot_chat_member.status == ChatMemberStatus.ADMINISTRATOR
                and (user_chat_member.status == ChatMemberStatus.ADMINISTRATOR or
                     user_chat_member.status == ChatMemberStatus.CREATOR)):
            # Если проверка прошла, продолжаем обработку
            await message.answer(f"Ви ввели канал: {channel_name}")
            dialog_manager.dialog_data["channel_name"] = channel_name

            # Отримуємо обрані теми з dialog_data
            selected_topics = dialog_manager.dialog_data.get("selected_topics", [])

            if selected_topics:
                try:
                    # Використовуємо async with для роботи з базою даних
                    async with get_data_serice() as db:
                        for topic_name in selected_topics:
                            news_id = await db.insert_news(
                                topic_name=topic_name,
                                channel_name=channel_name,
                                user_id=message.from_user.id,
                            )
                            await db.add_publish_date(news_id, ['everyday'])
                            await db.add_publish_time(news_id, ['every--hour'])
                    await message.answer("Підписка успішно збережена в базі даних!")
                except Exception as e:
                    await message.answer("❌ Сталася помилка при збереженні підписки.")
                    logging.error(f"Помилка збереження підписки: {e}")

            # Повертаємось до головного меню
            await dialog_manager.start(
                state=MainDialogSG.menu, mode=StartMode.RESET_STACK, show_mode=ShowMode.DELETE_AND_SEND
            )
        else:
            # Если пользователь или бот не администратор
            await message.answer(
                "❌ Ви не є адміністратором або власником цього каналу. Додавати підписки дозволено лише адміністраторам або власникам."
            )
    except Exception as e:
        await message.answer(
            "❌ Неможливо перевірити статус каналу. Переконайтесь, що ви ввели коректну назву каналу."
        )
        logging.error(f"Помилка перевірки каналу: {e}")

    # Повертаємось до головного меню
    await dialog_manager.start(
        state=MainDialogSG.menu, mode=StartMode.RESET_STACK, show_mode=ShowMode.DELETE_AND_SEND
    )



start_dialog = Dialog(
    Window(
        Const("Вас вітає новинний бот 📰!\n\n"
              "Наразі завдяки нашому боту ви можете:\n\n"
              "1️⃣ Створити нову підписку ✅\n"
              "2️⃣ Переглянути список підписок 📋\n"
              "➕ Додати опитування до новини\n"
              "␡ Видалити опитування\n"
              "␡ Видалити підписку\n"
              "♻️ Відновити підписку\n"
              "📰 Змінити тип відображення новин\n"
              "🧾🚀 Почати публікацію\n\n"
              "Для доступу до інших функцій натисніть кнопку меню нижче."),
        Row(
            Button(Const('Перейти до меню'), id='go_menu', on_click=switch_to_first_subscription),
        ),
        state=MainDialogSG.start
    ),
    Window(
        Const('<b>Ви знаходитесь в меню Підписок</b>\n'),
        Const('Ви можете перемикатися між вікнами поточного діалогу або перейти до нового 👇'),
        Row(
            Button(Const('Створити підписку'), id='w_second', on_click=switch_to_first_lists),
        ),
        Row(
            Button(Const('Переглянути Список підписок ▶️'), id='go_second_dialog', on_click=go_second_dialog),
        ),
        state=MainDialogSG.menu
    ),
    Window(
        Const('<b>Оберіть теми новин:</b>'),
        Column(
            Multiselect(
                checked_text=Format('✔️ {item[0]}'),
                unchecked_text=Format(' {item[0]}'),
                id='multi_topics',
                item_id_getter=operator.itemgetter(1),
                items="topics",
            ),
        ),
        Row(Button(Const('Підтвердити вибрані новини 📝'),
                   id='confirm_topics', on_click=confirm_selected_topics)),
        Row(Button(Const('Введіть свою новину 📝'),
                   id='enter_news', on_click=lambda callback, button,
                    dialog_manager: dialog_manager.switch_to(
                    state=MainDialogSG.enter_news))),
        Row(
            Button(Const('У 2-й діалог ▶️'), id='go_second_dialog', on_click=go_second_dialog),
            Button(Const('Скасувати'), id='cancel_to_subscription', on_click=return_to_subscription)
        ),
        state=MainDialogSG.new_subscription,
        getter=get_topics
    ),
    Window(
        Const("Будь ласка, введіть вашу новину:"),
        TextInput(
            id='news_input',
            type_factory=news_check,
            on_success=correct_news_handler,
            on_error=error_news_handler,
        ),
        state=MainDialogSG.enter_news
    ),
    Window(
        Const("Введіть назву новинного каналу на якому буде публікуватись новини:"),
        TextInput(
            id='channel_name_input',
            on_success=handle_channel_name
        ),
        Row(Button(Const('Повернутись в меню підписок'), id='cancel_to_subscription', on_click=return_to_subscription)),
        state=MainDialogSG.channel_name
    )
)

