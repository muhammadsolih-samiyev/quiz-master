from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
import json
import re

from keyboards.reply import get_cancel_menu, get_main_menu
from keyboards.inline import get_tests_keyboard, get_my_test_manage_keyboard
from database import add_test, get_public_tests, get_user_tests, get_test, delete_test
from utils.states import CreateTestState
from config import ADMINS

router = Router()

@router.message(F.text == "➕ Test yaratish")
async def start_create_test(message: Message, state: FSMContext):
    await message.answer("Test nomini kiriting:", reply_markup=get_cancel_menu())
    await state.set_state(CreateTestState.title)

@router.message(CreateTestState.title)
async def process_test_title(message: Message, state: FSMContext):
    await state.update_data(title=message.text)
    await message.answer("Test haqida qisqacha ma'lumot kiriting:")
    await state.set_state(CreateTestState.description)

@router.message(CreateTestState.description)
async def process_test_desc(message: Message, state: FSMContext):
    await state.update_data(description=message.text)
    await message.answer("Bitta savol uchun ajratiladigan vaqtni soniyalarda kiriting (masalan, 15 yoki 30):")
    await state.set_state(CreateTestState.time_limit)

@router.message(CreateTestState.time_limit)
async def process_test_time(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("Iltimos, vaqtni raqam bilan soniyalarda kiriting!")
        return
    
    time_limit = int(message.text)
    if time_limit < 10 or time_limit > 300:
        await message.answer("Vaqt 10 va 300 soniya oralig'ida bo'lishi kerak.")
        return
        
    await state.update_data(time_limit=time_limit)
    
    await message.answer(
        "Ajoyib! Endi test savollarini quyidagi formatda yuboring:\n\n"
        "1. Savol matni\n- Noto'g'ri javob\n+ To'g'ri javob\n- Noto'g'ri javob\n\n"
        "2. Ikkinchi savol...\n\n(Barcha savollarni bitta xabarda yozib yuboring)"
    )
    await state.set_state(CreateTestState.bulk_text)

@router.message(CreateTestState.bulk_text)
async def process_bulk_test(message: Message, state: FSMContext):
    data = await state.get_data()
    text = message.text.strip()
    
    questions = []
    current_q = None
    
    lines = text.split('\n')
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        if re.match(r'^\d+[\.\)]\s*', line):
            if current_q:
                if len(current_q['options']) >= 2 and current_q['correct'] != -1:
                    questions.append(current_q)
            
            q_text = re.sub(r'^\d+[\.\)]\s*', '', line)
            current_q = {'question': q_text, 'options': [], 'correct': -1}
            
        elif line.startswith('+'):
            if current_q:
                opt_text = line[1:].strip()
                current_q['options'].append(opt_text)
                current_q['correct'] = len(current_q['options']) - 1
                
        elif line.startswith('-'):
            if current_q:
                opt_text = line[1:].strip()
                current_q['options'].append(opt_text)
                
    if current_q and len(current_q['options']) >= 2 and current_q['correct'] != -1:
        questions.append(current_q)
        
    if not questions:
        await message.answer("Xatolik! Formatni tekshirib qaytadan yuboring. Hech qanday savol aniqlanmadi yoki to'g'ri javoblar (+) qo'yilmagan.")
        return
        
    is_public = message.from_user.id in ADMINS
    await add_test(
        author_id=message.from_user.id,
        title=data['title'],
        description=data['description'],
        questions=json.dumps(questions),
        time_limit=data['time_limit'],
        is_public=is_public
    )
    
    is_admin = message.from_user.id in ADMINS
    await state.clear()
    
    msg = f"✅ {len(questions)} ta savoldan iborat test muvaffaqiyatli yaratildi!\n\n"
    if is_public:
        msg += "U barcha foydalanuvchilarga ko'rinadi."
    else:
        msg += "Uni 'Mening testlarim' bo'limidan ko'rishingiz mumkin."
        
    await message.answer(msg, reply_markup=get_main_menu(is_admin))

@router.message(F.text == "📝 Testlar")
async def show_public_tests(message: Message, bot: Bot):
    tests = await get_public_tests()
    if not tests:
        await message.answer("Hozircha umumiy testlar mavjud emas.")
        return
    me = await bot.me()
    text = (
        "🎯 <b>Umumiy Testlar Bo'limi</b>\n\n"
        "<i>Bilimingizni sinash uchun eng qiziqarli testlar:</i>\n\n"
        "🧠 Turli sohalar bo'yicha savollar\n"
        "👥 Do'stlaringiz bilan guruhda bellashing\n"
        "📊 O'z natijalaringizni boshqalar bilan taqqoslang\n\n"
        "👇 Qatnashish uchun testni tanlang:"
    )
    await message.answer(text, reply_markup=get_tests_keyboard(tests, me.username, is_my_tests=False))

@router.message(F.text == "📊 Mening testlarim")
async def show_my_tests(message: Message, bot: Bot):
    tests = await get_user_tests(message.from_user.id)
    if not tests:
        await message.answer("Siz hali test yaratmagansiz.")
        return
    me = await bot.me()
    text = (
        "📂 <b>Sizning Testlaringiz</b>\n\n"
        "<i>Siz yaratgan barcha testlar shu yerda saqlanadi:</i>\n\n"
        "🔗 Testlarga ulashish havolasini olish\n"
        "🗑 Ularni boshqarish va o'chirish\n"
        "📈 Do'stlaringiz bilan testlarni o'tkazish\n\n"
        "👇 Boshqarish uchun testni tanlang:"
    )
    await message.answer(text, reply_markup=get_tests_keyboard(tests, me.username, is_my_tests=True))

@router.callback_query(F.data.startswith("mytest_"))
async def manage_my_test(callback: CallbackQuery, bot: Bot):
    test_id = int(callback.data.split("_")[1])
    test = await get_test(test_id)
    
    if not test or test['author_id'] != callback.from_user.id:
        await callback.answer("Test topilmadi yoki sizga tegishli emas!", show_alert=True)
        return
        
    questions = json.loads(test['questions'])
    me = await bot.me()
    
    text = (
        f"📝 <b>{test['title']}</b>\n\n"
        f"ℹ️ {test['description']}\n"
        f"⏱ Vaqt: bitta savol uchun {test['time_limit']} soniya\n"
        f"❓ Savollar soni: {len(questions)} ta\n\n"
        f"Boshqarish uchun quyidagi tugmalardan foydalaning:"
    )
    
    await callback.message.answer(text, reply_markup=get_my_test_manage_keyboard(test_id, me.username))
    await callback.answer()

@router.callback_query(F.data.startswith("deltest_"))
async def delete_test_handler(callback: CallbackQuery, bot: Bot):
    test_id = int(callback.data.split("_")[1])
    await delete_test(test_id, callback.from_user.id)
    
    await callback.message.delete()
    await callback.answer("Test o'chirildi!", show_alert=True)
