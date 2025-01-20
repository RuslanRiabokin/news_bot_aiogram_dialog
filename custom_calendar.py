from datetime import date
from typing import Dict
from aiogram_dialog import DialogManager
from aiogram_dialog.dialog import ChatEvent
from aiogram_dialog.widgets.kbd import CalendarScope, Calendar
from aiogram_dialog.widgets.kbd.calendar_kbd import (CalendarScopeView, CalendarDaysView,
                                                     DATE_TEXT, TODAY_TEXT, CalendarMonthView,
                                                     CalendarYearsView, ManagedCalendar)
from aiogram_dialog.widgets.text import Text, Format
from babel.dates import get_day_names, get_month_names



SELECTED_DAYS_KEY = "selected_dates"  # Ключ для збереження обраних дат

class WeekDay(Text):
    """Клас для відображення дня тижня з урахуванням локалі."""
    async def _render_text(self, data, manager: DialogManager) -> str:
        selected_date: date = data["date"]
        locale = manager.event.from_user.language_code
        return get_day_names(
            width="short", context='stand-alone', locale=locale,
        )[selected_date.weekday()].title()

class MarkedDay(Text):
    """Клас для маркування дати (наприклад, кружок чи точка)."""
    def __init__(self, mark: str, other: Text):
        super().__init__()
        self.mark = mark
        self.other = other

    async def _render_text(self, data, manager: DialogManager) -> str:
        current_date: date = data["date"]
        serial_date = current_date.isoformat()
        selected = manager.dialog_data.get(SELECTED_DAYS_KEY, [])
        if serial_date in selected:
            return f'<{current_date:%d}>'  # Повертаємо мітку для обраної дати
        return await self.other.render_text(data, manager)

class Month(Text):
    """Клас для відображення назви місяця з урахуванням локалі."""
    async def _render_text(self, data, manager: DialogManager) -> str:
        selected_date: date = data["date"]
        locale = manager.event.from_user.language_code
        return get_month_names(
            'wide', context='stand-alone', locale=locale,
        )[selected_date.month].title()

class CustomCalendar(Calendar):
    """Клас налаштованого календаря з кастомними мітками."""
    def _init_views(self) -> Dict[CalendarScope, CalendarScopeView]:
        return {
            CalendarScope.DAYS: CalendarDaysView(
                self._item_callback_data,
                date_text=MarkedDay("🔴", DATE_TEXT),  # Маркуємо обрані дати
                today_text=MarkedDay("⭕", TODAY_TEXT),  # Маркуємо сьогоднішню дату
                header_text="~~~~~ " + Month() + " ~~~~~",
                weekday_text=WeekDay(),
                next_month_text=Month() + " >>",
                prev_month_text="<< " + Month(),
            ),
            CalendarScope.MONTHS: CalendarMonthView(
                self._item_callback_data,
                month_text=Month(),
                header_text=Format("~~~~~ {date:%Y} ~~~~~"),
                this_month_text="[" + Month() + "]",
            ),
            CalendarScope.YEARS: CalendarYearsView(
                self._item_callback_data,
            ),
        }

async def on_date_selected(
    callback: ChatEvent,
    widget: ManagedCalendar,
    manager: DialogManager,
    clicked_date: date, /,
):
    selected = manager.dialog_data.setdefault(SELECTED_DAYS_KEY, [])
    serial_date = clicked_date.isoformat()
    if serial_date in selected:
        selected.remove(serial_date)
    else:
        selected.append(serial_date)


async def selection_getter(dialog_manager, **_):
    selected = dialog_manager.dialog_data.get(SELECTED_DAYS_KEY, [])
    return {
        "selected": ", ".join(sorted(selected)),
    }