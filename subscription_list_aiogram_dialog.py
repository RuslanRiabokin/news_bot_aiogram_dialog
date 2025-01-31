import logging
from aiogram.types import CallbackQuery
from aiogram_dialog import Dialog, Window, DialogManager, StartMode
from aiogram_dialog.widgets.kbd import Button, ScrollingGroup, Select, Row
from aiogram_dialog.widgets.text import Const, Format

from db_layer.database import AsyncDatabase
from db_layer.db_factory import get_data_serice
from states_class_aiogram_dialog import MainDialogSG, SecondDialogSG, EditSubscriptions


# Ініціалізація бази даних та логування
#db = AsyncDatabase()


async def close_second_dialog(callback: CallbackQuery, button: Button, dialog_manager: DialogManager):
    """Закриває другий діалог."""
    await dialog_manager.done()


async def switch_to_second_lists(callback: CallbackQuery, button: Button, dialog_manager: DialogManager):
    """Перехід на друге вікно другого діалогу."""
    await dialog_manager.switch_to(state=SecondDialogSG.second)


async def handle_subscription_click(callback: CallbackQuery, widget: Select, dialog_manager: DialogManager,
                                    item_id: str):
    """Обробляє натискання на кнопку підписки та зберігає item_id і topic_name у контексті."""
    # Приводимо item_id до цілого числа
    try:
        item_id = int(item_id)
    except ValueError:
        logging.error(f"Неправильний формат item_id: {item_id}")
        return

    # Отримуємо список підписок із контексту
    subscriptions = dialog_manager.dialog_data.get("subscriptions", [])

    # Шукаємо підписку за item_id (sub_id)
    selected_subscription = next((sub for sub in subscriptions if sub[0] == item_id), None)

    if selected_subscription:
        topic_name = selected_subscription[1]  # Назва підписки
        dialog_manager.dialog_data["item_id"] = item_id
        dialog_manager.dialog_data["topic_name"] = topic_name
        logging.info(f"Обрана підписка: {selected_subscription}")
    else:
        logging.error(f"Підписку з id {item_id} не знайдено!")

    await dialog_manager.switch_to(state=SecondDialogSG.second)


async def subscription_getter(dialog_manager: DialogManager, **kwargs):
    """Отримує підписки для користувача та логує їх."""
    user_id = dialog_manager.event.from_user.id
    logging.info(f"Отримуємо підписки для користувача з ID {user_id}")

    try:
        async with get_data_serice() as db:
            logging.info("Відкрито підключення до бази даних.")
            subscriptions = await db.get_subscriptions(user_id)
            logging.info(f"Отримані підписки з бази даних: {subscriptions}")
            dialog_manager.dialog_data["subscriptions"] = subscriptions

        # Генеруємо кнопки для кожної підписки або відображаємо повідомлення про відсутність підписок
        if subscriptions:
            buttons = [
                (f"{topic_name} - {channel_name} {is_active}", sub_id)
                for sub_id, topic_name, channel_name,_ , is_active in subscriptions
            ]
            logging.info(f"Кнопки, згенеровані для підписок: {buttons}")
            return {"subscriptions": buttons, "no_subscriptions": False}
        else:
            logging.info("Користувач не має активних підписок.")
            return {"subscriptions": [], "no_subscriptions": True}
    except Exception as e:
        logging.error(f"Помилка під час отримання підписок: {e}")
        return {"subscriptions": [], "no_subscriptions": True}



async def second_window_getter(dialog_manager: DialogManager, **kwargs):
    """Передає item_id та topic_name з контексту для відображення у другому вікні."""
    item_id = dialog_manager.dialog_data.get("item_id", "Невідома підписка")
    topic_name = dialog_manager.dialog_data.get("topic_name", "Невідома підписка")
    logging.info(f"Друге вікно: item_id={item_id}, topic_name={topic_name}")  # Логуємо значення
    return {"item_id": item_id, "topic_name": topic_name}


async def back_to_subscriptions(callback: CallbackQuery, button: Button, dialog_manager: DialogManager):
    """Повертає користувача до вікна з підписками."""
    await dialog_manager.switch_to(state=SecondDialogSG.first)


async def go_start(callback: CallbackQuery, button: Button, dialog_manager: DialogManager):
    """Повертає до початкового меню."""
    await dialog_manager.start(state=MainDialogSG.menu, mode=StartMode.RESET_STACK)


async def delete_subscription_message(
    callback: CallbackQuery, button: Button, dialog_manager: DialogManager
):
    """Видаляє підписку з бази даних та виводить повідомлення про видалення."""
    # Отримуємо item_id і topic_name з контексту
    item_id = dialog_manager.dialog_data.get("item_id", None)
    topic_name = dialog_manager.dialog_data.get("topic_name", "Невідома підписка")

    if item_id is None:
        logging.error("ID підписки не знайдено в контексті!")
        await callback.message.answer("⚠️ Помилка: ID підписки не знайдено.")
        return

    try:
        # Працюємо з базою даних через async with
        async with get_data_serice() as db:
            # Видаляємо підписку з бази даних
            await db.delete_news(item_id)
            logging.info(f"Підписка з ID {item_id} видалена з бази даних.")

            # Отримуємо оновлений список підписок
            subscriptions = await db.get_subscriptions(callback.from_user.id)

        # Повідомляємо користувача про успішне видалення
        await callback.message.answer(
            f"✅ Ви видалили підписку: <b>{item_id}</b> - <b>{topic_name}</b>"
        )

        # Оновлюємо список підписок у першому вікні
        dialog_manager.dialog_data["subscriptions"] = subscriptions

        # Повертаємо користувача до списку підписок
        await dialog_manager.switch_to(state=SecondDialogSG.first)

    except Exception as e:
        logging.error(f"Помилка під час видалення підписки з ID {item_id}: {e}")
        await callback.message.answer("❌ Сталася помилка при видаленні підписки.")


async def switch_to_edit_options(callback: CallbackQuery, button: Button, dialog_manager: DialogManager):
    """Перехід до вікна редагування підписок."""
    item_id = dialog_manager.dialog_data.get("item_id")
    async with get_data_serice() as db:
        sub_status = await db.get_subscription_status(item_id)
    await dialog_manager.start(state=EditSubscriptions.edit, mode=StartMode.NORMAL)
    dialog_manager.dialog_data["item_id"] = item_id
    dialog_manager.dialog_data["sub_status"] = sub_status[0]

# Визначення діалогу з підписками
current_subscriptions_dialog = Dialog(
    Window(
        Const('<b>Ви знаходитесь у меню ваших підписок!</b>\n'),
        # Відобразіть повідомлення про відсутність підписок, якщо їх немає
        Const('<b>У вас ще нема підписок</b>', when="no_subscriptions"),
        # Якщо підписки є, рендеримо ScrollingGroup
        ScrollingGroup(
            Select(
                Format('{item[0]}'),
                id='subscriptions',
                item_id_getter=lambda x: x[1],
                items='subscriptions',
                on_click=handle_subscription_click,
            ),
            id='subscriptions_group',
            width=1,
            height=4,
        ),
        Button(Const('Повернутись до меню'), id='button_cancel', on_click=close_second_dialog),
        state=SecondDialogSG.first,
        getter=subscription_getter  # Джерело даних для першого вікна
    ),
    Window(
        Format("<b>Меню новин:</b>\n <b>Ви обрали підписку: {item_id} {topic_name}</b>"),
        Row(
            Button(Const('Редагувати 📝'), id='edit_button', on_click=switch_to_edit_options),
            Button(Const('Видалити 📝'), id='delete_button', on_click=delete_subscription_message),
        ),
        Button(Const('Скасувати'), id='button_cancel', on_click=back_to_subscriptions),
        Button(Const('Повернутися до початкового меню'), id='button_start', on_click=go_start),
        state=SecondDialogSG.second,
        getter=second_window_getter  # Джерело даних для другого вікна
    )
)