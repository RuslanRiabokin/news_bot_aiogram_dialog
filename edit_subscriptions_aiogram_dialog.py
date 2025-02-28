from aiogram import F
from aiogram.types import CallbackQuery
from aiogram_dialog import Dialog, Window, DialogManager
from aiogram_dialog.widgets.input import TextInput
from aiogram_dialog.widgets.kbd import Button, Row, Group, Column
from aiogram_dialog.widgets.text import Const, Format

from custom_calendar import CustomCalendar, on_date_selected, selection_getter
from states_class_aiogram_dialog import EditSubscriptions, SecondDialogSG
from time_meneger import (on_time_success, time_getter, date_getter, time_date_getter,
                          date_selection_every_day,
                          finish_date_selection, time_selection_every_hour)


# Обробники дій з кнопками

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


async def switch_to_subscriptions(c: CallbackQuery, b: Button, d: DialogManager):
    await d.start(SecondDialogSG.first)  # Запускаем новое состояние


# Вікно вибору мови
select_language_window = Window(
    Const("<b>Виберіть мову:</b>"),
    Group(
        Row(
            Button(Const("🇺🇦 Українська"), id="uk", on_click=on_language_selected),
            Button(Const("🇬🇧󠁧󠁢󠁥󠁮󠁧󠁿 English"), id="en", on_click=on_language_selected),
        ),
        Row(
            Button(Const("🇷🇺 Русский"), id="ru", on_click=on_language_selected),
            Button(Const("🇩🇪 Deutsch"), id="de", on_click=on_language_selected),
        ),
    ),
    Button(Const("Назад"), id="back_to_edit", on_click=lambda c, b, d: d.switch_to(EditSubscriptions.edit)),
    state=EditSubscriptions.select_language,
)

# Головне вікно редагування підписки
edit_subscription_window = Window(
    Const("<b>Опції редагування підписки:</b>\n"),
    Button(Const("🕰 Час публікації"), id="change_time",
           on_click=lambda c, b, d: d.switch_to(EditSubscriptions.edit_time)),
    Button(Const("💬 Обрати мову"), id="select_language", on_click=select_language),
    Button(Const("📊 Додати опитування"), id="add_poll", on_click=add_poll),
    Button(Const("🐈 Вислати котика"), id="send_cat", on_click=send_cat),
    Row(
Button(Const('🗒 Мої підписки'), id='sub_list', on_click=switch_to_subscriptions),
        Button(Const("🔙"), id="back_button", on_click=back_to_subscription_details),
    ),
    state=EditSubscriptions.edit,
)



edit_time_window = Window(
    Const("<b>Редагування часу публікації:\n</b>"),
    Format("Обраний час: <b>{date} {time}</b>", when=F["date" or "time"]),
    Format("Ви не обрали <b>дату</b>", when=~F["date"]),
    Format("Ви не обрали <b>час</b>", when=~F["time"]),
    Row(
        Button(Const("⏰ Час публікації"), id="enter_time",
               on_click=lambda c, b, d: d.switch_to(EditSubscriptions.edit_t_time)),
        Button(Const("📆 Дата публікації"), id="enter_date",
               on_click=lambda c, b, d: d.switch_to(EditSubscriptions.edit_d_time)),
    ),
    Button(Const("🔙 Повернутися"), id="back_to_edit", on_click=lambda c, b, d: d.switch_to(EditSubscriptions.edit)),
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
    Button(Const("✔️ Обрати"), id="finish", on_click=finish_date_selection),
    Button(Const("🔙 Повернутися"), id="back_to_edit", on_click=lambda c, b, d: d.switch_to(EditSubscriptions.edit_d_time)),
    state=EditSubscriptions.calendar,
    getter=selection_getter
)

edit_d_time_window = Window(
    Const("<b>Редагування дат публікації:</b>"),
    Format("\nОбрані дати: <b>{date}</b>", when=F["date"]),
    Format("Ви не обрали <b>дату</b>", when=~F["date"]),
    Row(
        Button(Const("📅 Кожен день"), id="every_day",
               on_click=date_selection_every_day),
        Button(Const("👇 Обрати дату"), id="calendar",
               on_click=lambda c, b, d: d.switch_to(EditSubscriptions.calendar)),
    ),
    Button(Const("🔙 Повернутися"), id="back_to_edit", on_click=lambda c, b, d: d.switch_to(EditSubscriptions.edit_time)),
    state=EditSubscriptions.edit_d_time,
    getter=date_getter
)

edit_t_time_window = Window(
    Const("<b>Виберіть час публікації:</b>"),
    Format("\nОбраний час: <b>{time}</b>", when=F["time"]),
    Format("\nВи не обрали <b>час</b>", when=~F["time"]),
    Column(
        Button(Const("🕐 Кожну годину"), id="every_hour", on_click=lambda c, b, d: time_selection_every_hour(c, b, d, "")),
        Button(Const("🕒 Кожні 3 години"), id="every_3_hours",
               on_click=lambda c, b, d: time_selection_every_hour(c, b, d, "3")),
        Button(Const("🕕 Кожні 6 годин"), id="every_6_hours",
               on_click=lambda c, b, d: time_selection_every_hour(c, b, d, "6")),
    ),
    Row(
        Button(Const("✍️ Ввести час"), id="edit_time",
               on_click=lambda c, b, d: d.switch_to(EditSubscriptions.edit_time_write)),
    ),
    Button(Const("🔙 Повернутися"), id="back_to_edit", on_click=lambda c, b, d: d.switch_to(EditSubscriptions.edit_time)),
    state=EditSubscriptions.edit_t_time,
    getter=time_getter
)

edit_time_write_window = Window(
    Const("<b>Введіть час публікації:</b>\n\n"
          "Введіть у форматі '<b>9:30</b>' чи '<b>9:45, 13:15</b>'"),
    Format("Обраний час: <b>{time}</b>", when=F["time"]),
    Format("Ви не обрали <b>час</b>", when=~F["time"]),
    TextInput(
        id='news_input',
        on_success=on_time_success,
    ),
    Button(Const("🔙 Повернутися"), id="back_to_edit", on_click=lambda c, b, d: d.switch_to(EditSubscriptions.edit_t_time)),
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
