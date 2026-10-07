from aiogram import Router, F, Bot
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramAPIError
import asyncio

from config import ADMINS
from keyboards.reply import get_admin_menu, get_main_menu, get_cancel_menu
from keyboards.inline import get_channels_manage_keyboard
from database import count_users, get_all_users, get_channels, add_channel, remove_channel
from utils.states import BroadcastState, AddChannelState
from aiogram.types import CallbackQuery

router = Router()

@router.message(F.text == "⚙️ Admin panel")
async def admin_panel(message: Message):
    if message.from_user.id not in ADMINS:
        return
    await message.answer("Admin panelga xush kelibsiz!", reply_markup=get_admin_menu())

@router.message(F.text == "🔙 Asosiy menyu")
async def back_main_menu(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Asosiy menyu:", reply_markup=get_main_menu(is_admin=message.from_user.id in ADMINS))

@router.message(F.text == "👥 Foydalanuvchilar soni")
async def users_count_handler(message: Message):
    if message.from_user.id not in ADMINS:
        return
    count = await count_users()
    await message.answer(f"Botdagi umumiy foydalanuvchilar soni: {count} ta")

@router.message(F.text == "📢 Xabar yuborish")
async def start_broadcast(message: Message, state: FSMContext):
    if message.from_user.id not in ADMINS:
        return
    await message.answer("Barcha foydalanuvchilarga yuboriladigan xabarni kiriting:\n\n(Rasm, video va turli fayllar ham qo'llab-quvvatlanadi)", reply_markup=get_cancel_menu())
    await state.set_state(BroadcastState.text)

@router.message(BroadcastState.text)
async def process_broadcast(message: Message, state: FSMContext, bot: Bot):
    await state.clear()
    users = await get_all_users()
    await message.answer("Xabar yuborish boshlandi...", reply_markup=get_admin_menu())
    
    success = 0
    fail = 0
    for user in users:
        try:
            await bot.copy_message(
                chat_id=user['user_id'],
                from_chat_id=message.chat.id,
                message_id=message.message_id
            )
            success += 1
        except TelegramAPIError:
            fail += 1
        await asyncio.sleep(0.05)
        
    await message.answer(f"Xabar yuborish yakunlandi.\nMuvaffaqiyatli: {success}\nXatoliklar: {fail}")

@router.message(F.text == "🔗 Kanallarni boshqarish")
async def manage_channels_handler(message: Message):
    if message.from_user.id not in ADMINS:
        return
    channels = await get_channels()
    await message.answer("Majburiy kanallar ro'yxati (o'chirish uchun ustiga bosing):", reply_markup=get_channels_manage_keyboard(channels))

@router.callback_query(F.data == "add_channel")
async def start_add_channel(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await callback.message.answer("Qo'shmoqchi bo'lgan kanalingiz username'sini kiriting (masalan, @kanal_nomi):", reply_markup=get_cancel_menu())
    await state.set_state(AddChannelState.username)

@router.message(AddChannelState.username)
async def process_add_channel(message: Message, state: FSMContext):
    username = message.text
    if not username.startswith("@"):
        username = "@" + username
    
    await add_channel(username)
    await state.clear()
    await message.answer(f"{username} majburiy a'zolikka qo'shildi!", reply_markup=get_admin_menu())

@router.callback_query(F.data.startswith("delchan_"))
async def del_channel_handler(callback: CallbackQuery):
    username = callback.data.split("_", 1)[1]
    await remove_channel(username)
    
    channels = await get_channels()
    await callback.message.edit_reply_markup(reply_markup=get_channels_manage_keyboard(channels))
    await callback.answer(f"{username} o'chirildi!")

