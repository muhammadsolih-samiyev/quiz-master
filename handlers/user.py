from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from database import add_user
from keyboards.reply import get_main_menu
from config import ADMINS

router = Router()

@router.message(CommandStart())
async def start_handler(message: Message, state: FSMContext):
    await state.clear()
    await add_user(message.from_user.id, message.from_user.full_name, message.from_user.username)
    
    if message.chat.type != "private":
        return
        
    is_admin = message.from_user.id in ADMINS
    
    await message.answer(
        f"Assalomu alaykum, {message.from_user.full_name}! Botga xush kelibsiz.\nQuyidagi menyudan kerakli bo'limni tanlang:",
        reply_markup=get_main_menu(is_admin)
    )

@router.message(F.text == "❌ Bekor qilish")
async def cancel_handler(message: Message, state: FSMContext):
    await state.clear()
    is_admin = message.from_user.id in ADMINS
    await message.answer("Barcha amallar bekor qilindi.", reply_markup=get_main_menu(is_admin))

@router.callback_query(F.data == "check_sub")
async def check_sub_handler(callback: CallbackQuery):
    await callback.message.delete()
    is_admin = callback.from_user.id in ADMINS
    await callback.message.answer("A'zolik muvaffaqiyatli tasdiqlandi! Rahmat.", reply_markup=get_main_menu(is_admin))
    await callback.answer()
