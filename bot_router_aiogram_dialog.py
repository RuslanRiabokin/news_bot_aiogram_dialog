from aiogram import Dispatcher, Router
from aiogram.filters import CommandStart, Command
from aiogram.types import Message
from aiogram_dialog import DialogManager, StartMode, setup_dialogs, ShowMode
import asyncio
import logging

from bot_create_news_aiogram_dialog import start_dialog
from states_class_aiogram_dialog import MainDialogSG
from subscription_list_aiogram_dialog import current_subscriptions_dialog
from edit_subscriptions_aiogram_dialog import edit_subscription_dialog
from aiogram.types import FSInputFile
from instruction import INSTRUCTION_PDF_PATH



basic_commands_router = Router()


async def clear_previous_messages(dialog_manager: DialogManager, message: Message):
    """Видаляє всі повідомлення та завершує активний діалог."""
    try:
        # Завершуємо активний діалог, якщо він є
        await dialog_manager.reset_stack()
    except Exception as e:
        logging.exception("Помилка при скиданні діалогу:", exc_info=e)

    # Видаляємо останні повідомлення (наприклад, останні 10)
    chat_id = message.chat.id
    for i in range(10):  # Кількість повідомлень для видалення
        try:
            await message.bot.delete_message(chat_id, message.message_id - i)
        except Exception:
            continue  # Пропускаємо помилки, якщо повідомлення вже видалено

# Хендлер для команди /start
@basic_commands_router.message(CommandStart())
async def command_start_handler(message: Message, dialog_manager: DialogManager):
    """Запускає перший діалог при команді /start"""
    await clear_previous_messages(dialog_manager, message)
    await dialog_manager.start(MainDialogSG.start, mode=StartMode.RESET_STACK, show_mode=ShowMode.DELETE_AND_SEND)

# Хендлер для команди /menu
@basic_commands_router.message(Command("menu"))
async def menu_command_handler(message: Message, dialog_manager: DialogManager):
    """Хендлер для команди /menu, що відкриває вікно з меню підписок"""
    await clear_previous_messages(dialog_manager, message)
    await dialog_manager.start(MainDialogSG.menu, mode=StartMode.RESET_STACK, show_mode=ShowMode.DELETE_AND_SEND)


@basic_commands_router.message(Command("instruction"))
async def instruction_command_handler(message: Message):
    """Отправляет PDF инструкцию при команде /instruction"""
    try:
        pdf_file = FSInputFile(INSTRUCTION_PDF_PATH)
        await message.answer_document(pdf_file, caption="Ознайомтесь з інструкцією 📄")
    except FileNotFoundError:
        await message.answer("Файл інструкції не знайдено.")



def register_routes(dp: Dispatcher):
    # Реєстрація роутерів та діалогів
    dp.include_router(basic_commands_router)
    dp.include_routers(start_dialog, current_subscriptions_dialog, edit_subscription_dialog)
    setup_dialogs(dp)  # Налаштування системи діалогів
