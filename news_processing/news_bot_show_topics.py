from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
import html as ht

from db_layer.database import AsyncDatabase


async def new_show_topics(message: Message, user_id: int):
    """Показ підписок користувача."""
    async with AsyncDatabase() as db:
        subscriptions = await db.get_user_subscriptions(user_id)

        if not subscriptions:
            await message.answer("У вас немає активних підписок.")
        else:
            buttons = []  # Список кнопок

            for sub in subscriptions:
                subscription_id, topic, channel, is_active = sub[0], ht.escape(sub[1]), ht.escape(sub[2]), ht.escape(sub[5])
                button_text = f"ID {subscription_id}. Тема: {topic}, Канал: {channel}, статус: {is_active}"
                # Создаем кнопку для каждой подписки
                button = InlineKeyboardButton(text=button_text, callback_data=f"subscription_{subscription_id}")
                buttons.append([button])  # Добавляем кнопку как отдельный список в список кнопок

            # Добавляем кнопку "Назад до меню"
            buttons.append([InlineKeyboardButton(text="Назад до меню", callback_data="menu")])

            # Инициализируем клавиатуру с кнопками
            keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

            await message.answer("Ваші підписки:\nНатисніть на підписку."
                                 "\nВиберіть, що ви хочете з нею зробити",
                                 reply_markup=keyboard)

