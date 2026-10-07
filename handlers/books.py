from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from config import ADMINS
from keyboards.reply import get_cancel_menu, get_admin_menu, get_main_menu
from keyboards.inline import get_books_keyboard
from database import add_book, get_books, get_book
from utils.states import AddBookState

router = Router()

@router.message(F.text == "📚 Kitob qo'shish")
async def start_add_book(message: Message, state: FSMContext):
    if message.from_user.id not in ADMINS:
        return
    await message.answer("Kitob nomini kiriting:", reply_markup=get_cancel_menu())
    await state.set_state(AddBookState.title)

@router.message(AddBookState.title)
async def process_book_title(message: Message, state: FSMContext):
    await state.update_data(title=message.text)
    await message.answer("Kitob uchun tavsif kiriting:")
    await state.set_state(AddBookState.description)

@router.message(AddBookState.description)
async def process_book_desc(message: Message, state: FSMContext):
    await state.update_data(description=message.text)
    await message.answer("Endi kitob faylini yuboring (PDF, DOCX va hk.):")
    await state.set_state(AddBookState.file)

@router.message(AddBookState.file)
async def process_book_file(message: Message, state: FSMContext):
    if not message.document:
        await message.answer("Iltimos, fayl yuboring!")
        return
    
    data = await state.get_data()
    file_id = message.document.file_id
    
    await add_book(data['title'], file_id, data['description'])
    await state.clear()
    
    await message.answer("Kitob muvaffaqiyatli qo'shildi!", reply_markup=get_admin_menu())

@router.message(F.text == "📚 Kitoblar")
async def books_list(message: Message):
    books = await get_books()
    if not books:
        await message.answer("Hozircha kitoblar mavjud emas.")
        return
    
    text = (
        "📚 <b>Elektron Kitoblar Kutubxonasi</b>\n\n"
        "<i>Quyida siz uchun maxsus tanlangan kitoblar ro'yxati keltirilgan:</i>\n\n"
        "📖 O'qish uchun qulay formatlar\n"
        "🚀 Istalgan vaqtda yuklab oling\n"
        "💡 Bilimingizni oshiring va o'rganing\n\n"
        "👇 O'zingizga kerakli kitobni tanlang:"
    )
    await message.answer(text, reply_markup=get_books_keyboard(books))

@router.callback_query(F.data.startswith("book_"))
async def send_book(callback: CallbackQuery):
    book_id = int(callback.data.split("_")[1])
    book = await get_book(book_id)
    
    if not book:
        await callback.answer("Kitob topilmadi!")
        return
    
    text = f"📖 <b>{book['title']}</b>\n\n📝 {book['description']}"
    await callback.message.answer_document(document=book['file_id'], caption=text, parse_mode="HTML")
    await callback.answer()
