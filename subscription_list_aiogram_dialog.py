import logging
from aiogram.types import CallbackQuery
from aiogram_dialog import Dialog, Window, DialogManager, StartMode
from aiogram_dialog.widgets.kbd import Button, ScrollingGroup, Select, Row
from aiogram_dialog.widgets.text import Const, Format

from db_layer.db_factory import get_data_serice
from states_class_aiogram_dialog import MainDialogSG, SecondDialogSG, EditSubscriptions




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
    else:
        logging.error(f"Підписку з id {item_id} не знайдено!")

    await dialog_manager.switch_to(state=SecondDialogSG.second)


# Відповідність тем з емодзі
TOPIC_EMOJIS = {
    "IT": "📱",
    "Дизайн": "🎨",
    "Наука": "📖",
    "Суспільство": "👥",
    "Культура": "🗺",
    "Мистецтво": "🖌",
}

async def subscription_getter(dialog_manager: DialogManager, **kwargs):
    """Отримує підписки для користувача та додає емодзі до назв тем."""
    user_id = dialog_manager.event.from_user.id

    try:
        async with get_data_serice() as db:
            subscriptions = await db.get_subscriptions(user_id)
            dialog_manager.dialog_data["subscriptions"] = subscriptions

        # Генеруємо кнопки для підписок з емодзі
        if subscriptions:
            buttons = [
                (f"{TOPIC_EMOJIS.get(topic_name, '')} {topic_name} - {channel_name} {'🟢' if is_active else '🔴'}", sub_id)
                for sub_id, topic_name, channel_name, _, is_active in subscriptions
            ]
            return {"subscriptions": buttons, "no_subscriptions": False}
        else:
            return {"subscriptions": [], "no_subscriptions": True}
    except Exception as e:
        logging.error(f"Помилка під час отримання підписок: {e}")
        return {"subscriptions": [], "no_subscriptions": True}


async def second_window_getter(dialog_manager: DialogManager, **kwargs):
    """Отримує інформацію про вибрану підписку та додає емодзі до назв тем."""
    item_id = dialog_manager.dialog_data.get("item_id", "Невідома підписка")
    topic_name = dialog_manager.dialog_data.get("topic_name", "Невідома тема")

    # Додаємо емодзі до теми
    topic_name_with_emoji = f"{TOPIC_EMOJIS.get(topic_name, '')} {topic_name}"

    return {"item_id": item_id, "topic_name": topic_name_with_emoji}



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

async def run_publication(callback: CallbackQuery, button: Button, dialog_manager: DialogManager):
    sub_id = dialog_manager.dialog_data.get('item_id')
    async with get_data_serice() as db:
        sub_status = (await db.get_subscription_status(sub_id))[0]
        dialog_manager.dialog_data['sub_status'] = sub_status
        if sub_status != 'pause':
            await callback.message.answer("Публікація вже розпочата")
        else:
            await db.set_subscription_status(status='yes', sub_id=sub_id)
            await callback.message.answer("▶ Публікація розпочата.")

async def stop_publication(callback: CallbackQuery, button: Button, dialog_manager: DialogManager):
    sub_id = dialog_manager.dialog_data.get('item_id')
    async with get_data_serice() as db:
        sub_status = (await db.get_subscription_status(sub_id))[0]
        dialog_manager.dialog_data['sub_status'] = sub_status
        if sub_status != 'yes':
            await callback.message.answer("Публікація вже призупинена")
        else:
            await db.set_subscription_status(status='pause', sub_id=sub_id)
            await callback.message.answer("▶ Публікація призупинена.")


# Визначення діалогу з підписками
current_subscriptions_dialog = Dialog(
    Window(
        Const('Тут ти можеш переглянути існуючі <b>підписки:</b>\n'),
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
        Button(Const('🔙 Повернутись'), id='button_cancel', on_click=close_second_dialog),
        state=SecondDialogSG.first,
        getter=subscription_getter  # Джерело даних для першого вікна
    ),
    Window(
        Format("<b>Меню новин:</b>\n <b>Ви обрали підписку: {item_id} {topic_name}</b>"),
        Row(
            Button(Const('🖊 Редагувати'), id='edit_button', on_click=switch_to_edit_options),
            Button(Const('❌ Видалити'), id='delete_button', on_click=delete_subscription_message),
        ),
        Row(
            Button(Const('🛑 Призупинити'), id='stop_pub', on_click=stop_publication),
            Button(Const('♻️ Відновити'), id='run_pub', on_click=run_publication),
        ),
        Button(Const('🗒 Мої підписки'), id='sub_list',
               on_click=lambda c, b, d: d.switch_to(SecondDialogSG.first)),
        state=SecondDialogSG.second,
        getter=second_window_getter  # Джерело даних для другого вікна
    )
)
