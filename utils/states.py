from aiogram.fsm.state import State, StatesGroup

class BroadcastState(StatesGroup):
    text = State()

class AddBookState(StatesGroup):
    title = State()
    description = State()
    file = State()

class CreateTestState(StatesGroup):
    title = State()
    description = State()
    time_limit = State()
    bulk_text = State()

class TakeTestState(StatesGroup):
    test_id = State()
    current_question = State()
    answers = State()

class AddChannelState(StatesGroup):
    username = State()

