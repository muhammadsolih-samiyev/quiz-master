from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def get_main_menu(is_admin=False):
    keyboard = [
        [KeyboardButton(text="📚 Kitoblar"), KeyboardButton(text="📝 Testlar")],
        [KeyboardButton(text="➕ Test yaratish"), KeyboardButton(text="📊 Mening testlarim")],
    ]
    if is_admin:
        keyboard.append([KeyboardButton(text="⚙️ Admin panel")])
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

def get_admin_menu():
    keyboard = [
        [KeyboardButton(text="👥 Foydalanuvchilar soni"), KeyboardButton(text="📢 Xabar yuborish")],
        [KeyboardButton(text="📚 Kitob qo'shish"), KeyboardButton(text="🔗 Kanallarni boshqarish")],
        [KeyboardButton(text="🔙 Asosiy menyu")]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

def get_cancel_menu():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="❌ Bekor qilish")]],
        resize_keyboard=True
    )
