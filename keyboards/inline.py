from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

def get_subscription_keyboard(channels):
    builder = InlineKeyboardBuilder()
    for i, channel in enumerate(channels, start=1):
        builder.button(text=f"📢 {i}-Kanalga a'zo bo'lish", url=f"https://t.me/{channel.replace('@', '')}")
    builder.button(text="✅ A'zolikni tekshirish", callback_data="check_sub")
    builder.adjust(1)
    return builder.as_markup()

def get_books_keyboard(books):
    builder = InlineKeyboardBuilder()
    for book in books:
        builder.button(text=f"📖 {book['title']}", callback_data=f"book_{book['id']}")
    builder.adjust(1)
    return builder.as_markup()

def get_tests_keyboard(tests, bot_username, is_my_tests=False):
    builder = InlineKeyboardBuilder()
    for test in tests:
        if is_my_tests:
            builder.button(text=f"📝 {test['title']}", callback_data=f"mytest_{test['id']}")
        else:
            builder.button(text=f"📝 {test['title']}", url=f"https://t.me/{bot_username}?start=test_{test['id']}")
    builder.adjust(1)
    return builder.as_markup()

def get_my_test_manage_keyboard(test_id, bot_username):
    builder = InlineKeyboardBuilder()
    builder.button(text="▶️ O'zim ishlash", url=f"https://t.me/{bot_username}?start=test_{test_id}")
    builder.button(text="👥 Guruhga yuborish", url=f"https://t.me/{bot_username}?startgroup=test_{test_id}")
    builder.button(text="❌ O'chirish", callback_data=f"deltest_{test_id}")
    builder.adjust(1)
    return builder.as_markup()
    
def get_test_question_keyboard(options):
    builder = InlineKeyboardBuilder()
    letters = ['A', 'B', 'C', 'D', 'E']
    for i, opt in enumerate(options):
        builder.button(text=f"{letters[i]}) {opt}", callback_data=f"answer_{i}")
    builder.adjust(1)
    return builder.as_markup()

def get_channels_manage_keyboard(channels):
    builder = InlineKeyboardBuilder()
    for channel in channels:
        builder.button(text=f"🗑 {channel}", callback_data=f"delchan_{channel}")
    builder.button(text="➕ Kanal qo'shish", callback_data="add_channel")
    builder.adjust(1)
    return builder.as_markup()
