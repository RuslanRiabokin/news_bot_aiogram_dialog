import re
from datetime import datetime

from aiogram.types import Message, CallbackQuery
from aiogram_dialog import DialogManager
from aiogram_dialog.widgets.input import ManagedTextInput
from aiogram_dialog.widgets.kbd import Button

from db_layer.db_factory import get_data_serice
from states_class_aiogram_dialog import EditSubscriptions


async def on_time_success(message: Message, widget: ManagedTextInput,
                          dialog_manager: DialogManager, text: str):
    """Функція перевіряє та виправляє формат часу, фільтруючи некоректні значення."""
    time_pattern = r"^(?:[01]\d|2[0-3]):[0-5]\d$"  # Години: 00-23, хвилини: 00-59
    sub_id = dialog_manager.dialog_data.get('item_id', None)

    if isinstance(text, str):
        text = re.split(r"[ ]+", text)
        text = [t.strip() for t in text if t.strip()]


    corrected_times = []
    for time in text:
        # Перевірка на букви або інші неприпустимі символи
        if any(char.isalpha() for char in time):
            await message.answer(
                "Ви ввели невірний формат часу. "
                "Час не може містити букви чи інші неприпустимі символи."
            )
            return

        # Якщо введені лише години (наприклад, "12"), додаємо ":00"
        if re.match(r"^\d{1,2}$", time):
            time = f"{int(time):02d}:00"
        # Якщо час у форматі "1230", виправляємо на "12:30"
        elif re.match(r"^\d{3,4}$", time):
            hours = int(time[:-2])  # Перші цифри - години
            minutes = int(time[-2:])  # Останні цифри - хвилини
            if 0 <= hours <= 23 and 0 <= minutes <= 59:
                time = f"{hours:02d}:{minutes:02d}"
            else:
                await message.answer(
                    "Ви ввели невірний формат часу."
                    "Формат має бути HH:MM (наприклад, '14:30' чи '14,30, 14:45')."
                )
                return
        # Якщо час містить кому або інший неприпустимий знак, виправляємо
        elif re.match(r"^\d{1,2}[^\d:]\d{2}$", time):
            time = time.replace(",", ":").replace(".", ":").replace(";", ":")
            if not re.match(time_pattern, time):
                await message.answer(
                    "Ви ввели невірний формат часу."
                    "Формат має бути HH:MM (наприклад, '14:30' чи '14,30, 14:45')."
                )
                return
        # Якщо час не відповідає жодному формату
        elif not re.match(time_pattern, time):
            await message.answer(
                "Ви ввели невірний формат часу."
                "Формат має бути HH:MM (наприклад, '14:30' чи '14,30, 14:45')."
            )
            return
        corrected_times.append(time)

    async with get_data_serice() as db:
        pub_times = await db.get_publish_time(sub_id)

        db_times = {pub_time[0] for pub_time in pub_times}
        corrected_times = [t for t in corrected_times if t not in db_times]

        for pub_time in pub_times:
            if pub_time[0] in ['every--hour', 'every-3-hour', 'every-6-hour']:
                await db.delete_times(sub_id)

        corrected_times = sorted(corrected_times, key=lambda t: datetime.strptime(t, "%H:%M"))

        await db.add_publish_time(sub_id, corrected_times)

    await message.delete()
    await dialog_manager.switch_to(EditSubscriptions.edit_time_write)


async def time_selection_every_hour(callback: CallbackQuery, button: Button, dialog_manager: DialogManager,
                                    number: str = None):
    sub_id = dialog_manager.dialog_data.get("item_id", None)
    async with get_data_serice() as db:
        await db.delete_times(sub_id)
        await db.add_publish_time(sub_id, [f'every-{number}-hour'])
    await dialog_manager.switch_to(EditSubscriptions.edit_t_time)


async def time_getter(dialog_manager: DialogManager, **_):
    sub_id = dialog_manager.dialog_data.get('item_id', None)
    async with get_data_serice() as db:
        time = await db.get_publish_time(sub_id)  # [('every--hour',)]
    if time[0][0] == 'every--hour':
        return {'time': 'Кожну годину'}
    elif time[0][0] == 'every-3-hour':
        return {'time': 'Кожні 3 години'}
    elif time[0][0] == 'every-6-hour':
        return {'time': 'Кожні 6 годин'}
    else:
        return {"time": ", ".join(t[0] for t in time)}


async def date_getter(dialog_manager: DialogManager, **_):
    sub_id = dialog_manager.dialog_data.get("item_id", None)
    async with get_data_serice() as db:
        date = await db.get_publish_date(sub_id)  # [('everyday',)]
    if date[0][0] == 'everyday':
        return {'date': 'Кожного дня'}
    else:
        return {'date': ', '.join(d[0] for d in date)}


async def time_date_getter(dialog_manager: DialogManager, **_):
    date = await date_getter(dialog_manager, **_)
    time = await time_getter(dialog_manager, **_)
    return {**date, **time}


async def date_selection_every_day(callback: CallbackQuery, button: Button, dialog_manager: DialogManager):
    sub_id = dialog_manager.dialog_data.get("item_id", None)
    async with get_data_serice() as db:
        await db.delete_dates(sub_id)
        await db.add_publish_date(sub_id, ['everyday'])
    await dialog_manager.switch_to(EditSubscriptions.edit_d_time)


async def finish_date_selection(callback: CallbackQuery, button: Button, manager: DialogManager):
    """Завершення вибору дат та виведення остаточного списку."""
    sub_id = manager.dialog_data.get('item_id')
    selected_dates = manager.dialog_data.get("selected_dates", [])
    async with get_data_serice() as db:
        dates = await db.get_publish_date(sub_id)
        for date in dates:
            if date[0] == 'everyday':
                await db.delete_dates(sub_id)
                break
        await db.add_publish_date(sub_id, selected_dates)
    dates_text = ", ".join([str(d) for d in selected_dates])
    await callback.message.answer(f"Ваш остаточний вибір: {dates_text}")
    await manager.switch_to(EditSubscriptions.edit_d_time)
