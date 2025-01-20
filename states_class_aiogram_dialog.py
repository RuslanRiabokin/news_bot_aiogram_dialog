from aiogram.fsm.state import State, StatesGroup

class MainDialogSG(StatesGroup):
    start = State()
    menu = State()
    new_subscription = State()
    enter_news = State()
    channel_name = State()

class SecondDialogSG(StatesGroup):
    first = State()
    second = State()

class EditSubscriptions(StatesGroup):
    select_language = State()
    edit = State()
    edit_time = State()
    edit_d_time = State()
    edit_t_time = State()
    edit_time_write = State()
    calendar = State()
