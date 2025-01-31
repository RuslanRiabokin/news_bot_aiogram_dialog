import logging
from aiogram import F
from aiogram.types import CallbackQuery
from aiogram_dialog import Dialog, Window, DialogManager
from aiogram_dialog.widgets.input import TextInput
from aiogram_dialog.widgets.kbd import Button, Row, Group
from aiogram_dialog.widgets.text import Const, Format

from db_layer.db_factory import get_data_serice
from time_meneger import on_time_success, time_getter, date_getter,time_date_getter ,date_selection_every_day, finish_date_selection,time_selection_every_hour
from states_class_aiogram_dialog import EditSubscriptions, SecondDialogSG
from subscription_list_aiogram_dialog import go_start
from custom_calendar import CustomCalendar, on_date_selected, selection_getter
from db_layer.database import AsyncDatabase



# Обробники дій з кнопками
async def edit_publication_time(callback: CallbackQuery, button: Button, dialog_manager: DialogManager):
    await callback.message.answer("🕒 Час публікації буде змінено.")


async def pause_or_run_publication(callback: CallbackQuery, button: Button, dialog_manager: DialogManager):
    sub_id = dialog_manager.dialog_data.get('item_id')
    async with get_data_serice() as db:
        sub_status = (await db.get_subscription_status(sub_id))[0]
        dialog_manager.dialog_data['sub_status'] = sub_status
        if sub_status == '🟢':
            await db.set_subscription_status(status='pause', sub_id=sub_id)
            await callback.message.answer("⏸ Публікацію призупинено.")
        elif sub_status == 'pause':
            await db.set_subscription_status(status='🟢', sub_id=sub_id)
            await callback.message.answer("▶ Публікація розпочата.")
        else:
            logging.error(f'Неправильний статус новини {sub_status}')
            await callback.message.answer("Неправильний статус новини.")
    await dialog_manager.switch_to(EditSubscriptions.edit)


async def dialog_data_getter(dialog_manager: DialogManager, **kwargs):
    """Передаёт статус публикации в данные для отображения кнопки."""
    sub_id = dialog_manager.dialog_data.get('item_id')
    sub_status = dialog_manager.dialog_data.get("sub_status")  # Статус по умолчанию
    sub_status_text = ("Розпочати публікацію ▶" if sub_status == "🟢" else "Призупинити публікацію ⏸")
    return {"publication_status": sub_status, "publication_status_text": sub_status_text}


async def add_poll(callback: CallbackQuery, button: Button, dialog_manager: DialogManager):
    await callback.message.answer("📊 Опитування додано.")


async def send_cat(callback: CallbackQuery, button: Button, dialog_manager: DialogManager):
    await callback.message.answer("Ось ваш котик! 🐈")
    await callback.answer()


# Словник перекладів повідомлень
MESSAGES = {
    "uk": "Ви обрали мову: Українська",
    "en": "You selected the language: English",
    "ru": "Вы выбрали: Русский",
    "de": "Sie haben die Sprache gewählt: Deutsch",
}


async def on_language_selected(callback: CallbackQuery, button: Button, dialog_manager: DialogManager):
    """Обробка вибору мови з відображенням повідомлення на вибраній мові."""
    selected_language = button.widget_id  # ID кнопки як код мови
    message = MESSAGES.get(selected_language,
                           f"Selected language: {selected_language}")  # Беремо повідомлення або дефолтне

    await callback.message.answer(message)  # Надсилаємо повідомлення на потрібній мові
    await dialog_manager.switch_to(EditSubscriptions.edit)  # Повертаємося в меню редагування


async def select_language(callback: CallbackQuery, button: Button, dialog_manager: DialogManager):
    """Перехід до вікна вибору мови."""
    await dialog_manager.switch_to(EditSubscriptions.select_language)


async def back_to_subscription_details(callback: CallbackQuery, button: Button, dialog_manager: DialogManager):
    """Повернення до деталей підписки."""
    await dialog_manager.done()
    await dialog_manager.switch_to(SecondDialogSG.second)


# Вікно вибору мови
select_language_window = Window(
    Const("<b>Виберіть мову:</b>"),
    Group(
        Row(
            Button(Const("Українська"), id="uk", on_click=on_language_selected),
            Button(Const("English"), id="en", on_click=on_language_selected),
        ),
        Row(
            Button(Const("Русский"), id="ru", on_click=on_language_selected),
            Button(Const("Deutsch"), id="de", on_click=on_language_selected),
        ),
    ),
    Button(Const("Назад"), id="back_to_edit", on_click=lambda c, b, d: d.switch_to(EditSubscriptions.edit)),
    state=EditSubscriptions.select_language,
)

# Головне вікно редагування підписки
edit_subscription_window = Window(
    Const("<b>Опції редагування підписки</b>\n"),
    Row(
        Button(Const("Редагувати час публікації 🕒"), id="change_time",
               on_click=lambda c, b, d: d.switch_to(EditSubscriptions.edit_time)),
    ),
    Row(
        Button(Format("{publication_status_text}"), id="pause_or_run_publication", on_click=pause_or_run_publication),
        Button(Const("Додати опитування 📊"), id="add_poll", on_click=add_poll),
    ),
    Row(
        Button(Const("Вибрати мову"), id="select_language", on_click=select_language),
        Button(Const("Вислати котика 🐈"), id="send_cat", on_click=send_cat),
    ),
    Button(Const("Повернутись назад"), id="back_button", on_click=back_to_subscription_details),
    Button(Const("Повернутися до початкового меню"), id="button_start", on_click=go_start),
    state=EditSubscriptions.edit,
    getter=dialog_data_getter,
)

"""# Об'єднання всіх вікон в один діалог
edit_subscription_dialog = Dialog(
    edit_subscription_window,
    select_language_window,
)"""

edit_time_window = Window(
    Const("<b>Редагування часу публікації:</b>"),
    Format("\nSelected date: {date}", when=F["date"]),
    Format("\nNo date selected", when=~F["date"]),
    Format("\nSelected Time: {time}", when=F["time"]),
    Format("\nNo time selected", when=~F["time"]),
    Row(
        Button(Const("Обрати час публікації"), id="enter_time",
               on_click=lambda c, b, d: d.switch_to(EditSubscriptions.edit_t_time)),
        Button(Const("Обрати дату публікації"), id="enter_date",
               on_click=lambda c, b, d: d.switch_to(EditSubscriptions.edit_d_time)),
    ),
    Button(Const("Назад"), id="back_to_edit", on_click=lambda c, b, d: d.switch_to(EditSubscriptions.edit)),
    state=EditSubscriptions.edit_time,
    getter=time_date_getter
)

# Вікно з кастомним календарем
calendar_window = Window(
    Const("<b>Оберіть дати:</b>"),
    Format("\nSelected: {selected}", when=F["selected"]),
    Format("\nNo dates selected", when=~F["selected"]),
    CustomCalendar(
        id="calendar",
        on_click=on_date_selected,
    ),
    Button(Const("Завершити вибір"), id="finish", on_click=finish_date_selection),
    Button(Const("Назад"), id="back_to_edit", on_click=lambda c, b, d: d.switch_to(EditSubscriptions.edit_d_time)),
    state=EditSubscriptions.calendar,
    getter=selection_getter
)

edit_d_time_window = Window(
    Const("<b>Редагування дат публікації:</b>"),
    Format("\nSelected date: {date}", when=F["date"]),
    Format("\nNo date selected", when=~F["date"]),
    Row(
        Button(Const("Публікація кожен день"), id="every_day",
               on_click=date_selection_every_day),
        Button(Const("Обрати дату самому"), id="calendar",
               on_click=lambda c, b, d: d.switch_to(EditSubscriptions.calendar)),
    ),
    Button(Const("Назад"), id="back_to_edit", on_click=lambda c, b, d: d.switch_to(EditSubscriptions.edit_time)),
    state=EditSubscriptions.edit_d_time,
    getter=date_getter
)

edit_t_time_window = Window(
    Const("Виберіть час публікації:"),
    Format("\nSelected Time: {time}", when=F["time"]),
    Format("\nNo time selected", when=~F["time"]),
    Row(
        Button(Const("Кожну годину"), id="every_hour", on_click=lambda c, b, d: time_selection_every_hour(c, b, d, "")),
        Button(Const("Кожні 2 години"), id="every_2_hours", on_click=lambda c, b, d: time_selection_every_hour(c, b, d, "2")),
        Button(Const("Кожні 3 години"), id="every_3_hours", on_click=lambda c, b, d: time_selection_every_hour(c, b, d, "3")),
    ),
    Row(
    Button(Const("Ввести час самому"), id="edit_time", on_click=lambda c, b, d: d.switch_to(EditSubscriptions.edit_time_write)),
    ),
    Button(Const("Назад"), id="back_to_edit", on_click=lambda c, b, d: d.switch_to(EditSubscriptions.edit_time)),
    state=EditSubscriptions.edit_t_time,
    getter=time_getter
)

edit_time_write_window = Window(
    Const("Введіть час публікації:\n"
      "Якщо хочете ввести кілька часів публікації,\n"
      "<b>введіть у такому форматі 9.30 12.45</b>"),
    Format("\nSelected Time: {time}", when=F["time"]),
    Format("\nNo time selected", when=~F["time"]),
    TextInput(
        id='news_input',
        on_success=on_time_success,
    ),
    Button(Const("Назад"), id="back_to_edit", on_click=lambda c, b, d: d.switch_to(EditSubscriptions.edit_t_time)),
    state=EditSubscriptions.edit_time_write,
    getter=time_getter
)

# Об'єднання вікон у діалог
edit_subscription_dialog = Dialog(
    edit_subscription_window,
    edit_time_window,
    edit_d_time_window,
    edit_t_time_window,
    edit_time_write_window,
    select_language_window,
    calendar_window,
)
