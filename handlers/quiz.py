import asyncio
import json
from aiogram import Router, F, Bot
from aiogram.filters import Command, CommandObject
from aiogram.types import Message, CallbackQuery, PollAnswer
from aiogram.utils.keyboard import InlineKeyboardBuilder
from database import get_test, save_test_result
from config import ADMINS

router = Router()

# In-memory storage for active quizzes
group_quizzes = {}
private_quizzes = {}

@router.message(Command("start"), F.text.contains("test_"))
async def start_quiz_deep_link(message: Message, command: CommandObject, bot: Bot):
    args = command.args
    if not args or not args.startswith("test_"):
        return
        
    test_id = int(args.split("_")[1])
    test = await get_test(test_id)
    if not test:
        await message.answer("Test topilmadi!")
        return
        
    questions = json.loads(test['questions'])
    if not questions:
        await message.answer("Testda savollar yo'q!")
        return
        
    is_group = message.chat.type in ["group", "supergroup"]
    
    if is_group:
        if message.chat.id in group_quizzes:
            await message.answer("Bu guruhda allaqachon test boshlangan! Uni tugashini kuting.")
            return
            
        group_quizzes[message.chat.id] = {
            'test_id': test_id,
            'test_title': test['title'],
            'time_limit': test['time_limit'],
            'questions': questions,
            'participants': {},
            'scores': {},
            'status': 'lobby',
            'admin': message.from_user.id
        }
        
        builder = InlineKeyboardBuilder()
        builder.button(text="I am ready!", callback_data="quiz_join")
        builder.adjust(1)
        
        await message.answer(
            f"🎲 <b>{test['title']}</b> testiga tayyorlaning!\n\n"
            f"🖊 {len(questions)} ta savol\n"
            f"⏱ Har bir savolga {test['time_limit']} soniya\n"
            f"👀 Barcha guruh a'zolariga natijalar ko'rinadi\n\n"
            f"🏁 Kamida 2 kishi tayyor bo'lganda test boshlanadi.\n"
            f"🛑 Testni to'xtatish uchun /stop ni bosing.",
            reply_markup=builder.as_markup()
        )
    else:
        await message.answer(f"📝 {test['title']} testini boshlaymiz!\n\nHar bir savol uchun {test['time_limit']} soniya vaqt beriladi.")
        await asyncio.sleep(2)
        await send_private_poll(message.chat.id, test_id, test['title'], questions, 0, 0, test['time_limit'], bot)

async def send_private_poll(chat_id, test_id, test_title, questions, q_idx, current_score, time_limit, bot: Bot):
    q = questions[q_idx]
    poll_msg = await bot.send_poll(
        chat_id=chat_id,
        question=f"({q_idx+1}/{len(questions)}) {q['question']}",
        options=q['options'],
        type="quiz",
        correct_option_id=q['correct'],
        is_anonymous=False,
        open_period=time_limit
    )
    
    private_quizzes[poll_msg.poll.id] = {
        'chat_id': chat_id,
        'test_id': test_id,
        'test_title': test_title,
        'q_idx': q_idx,
        'questions': questions,
        'score': current_score,
        'time_limit': time_limit
    }

@router.poll_answer()
async def handle_poll_answer(poll_answer: PollAnswer, bot: Bot):
    poll_id = poll_answer.poll_id
    user_id = poll_answer.user.id
    
    if poll_id in private_quizzes:
        quiz = private_quizzes[poll_id]
        q_idx = quiz['q_idx']
        q = quiz['questions'][q_idx]
        
        if poll_answer.option_ids[0] == q['correct']:
            quiz['score'] += 1
            
        next_idx = q_idx + 1
        total = len(quiz['questions'])
        
        await asyncio.sleep(1.5)
        
        if next_idx < total:
            await send_private_poll(quiz['chat_id'], quiz['test_id'], quiz['test_title'], quiz['questions'], next_idx, quiz['score'], quiz['time_limit'], bot)
        else:
            percent = int((quiz['score'] / total) * 100)
            result_text = (
                f"🎯 Test yakunlandi!\n\n"
                f"📊 Natijangiz: {quiz['score']}/{total} ({percent}%)\n\n"
            )
            if percent >= 80:
                result_text += "🌟 Juda zo'r natija!"
            elif percent >= 60:
                result_text += "👍 Yaxshi natija!"
            else:
                result_text += "📚 Ko'proq o'qib, tayyorgarlik ko'rish kerak."
                
            me = await bot.me()
            from urllib.parse import quote
            share_text = f"Men '{quiz['test_title']}' testida {quiz['score']}/{total} natija ko'rsatdim! Siz ham sinab ko'ring."
            test_link = f"https://t.me/{me.username}?start=test_{quiz['test_id']}"
            share_url = f"https://t.me/share/url?url={test_link}&text={quote(share_text)}"
            
            builder = InlineKeyboardBuilder()
            builder.button(text="↗️ Natijani ulashish", url=share_url)
                
            await bot.send_message(quiz['chat_id'], result_text, reply_markup=builder.as_markup())
            await save_test_result(quiz['test_id'], user_id, quiz['score'], total)
            
        del private_quizzes[poll_id]
        return
        
    for chat_id, g_quiz in group_quizzes.items():
        if g_quiz['status'] == 'running' and g_quiz.get('current_poll_id') == poll_id:
            if user_id in g_quiz['participants']:
                q_idx = g_quiz['current_q_idx']
                q = g_quiz['questions'][q_idx]
                if poll_answer.option_ids[0] == q['correct']:
                    g_quiz['scores'][user_id] += 1
            break

@router.callback_query(F.data == "quiz_join")
async def join_group_quiz(callback: CallbackQuery, bot: Bot):
    chat_id = callback.message.chat.id
    if chat_id not in group_quizzes or group_quizzes[chat_id]['status'] != 'lobby':
        await callback.answer("Bu test yopilgan yoki allaqachon boshlangan!", show_alert=True)
        return
        
    user_id = callback.from_user.id
    name = callback.from_user.full_name
    
    if user_id in group_quizzes[chat_id]['participants']:
        await callback.answer("Siz allaqachon tayyorsiz!", show_alert=True)
        return
        
    group_quizzes[chat_id]['participants'][user_id] = name
    if user_id not in group_quizzes[chat_id]['scores']:
        group_quizzes[chat_id]['scores'][user_id] = 0
    
    count = len(group_quizzes[chat_id]['participants'])
    await callback.answer(f"Siz tayyorsiz! Jami tayyorlar: {count}")
    
    if count >= 2:
        quiz = group_quizzes[chat_id]
        quiz['status'] = 'running'
        await callback.message.delete()
        
        await callback.message.answer(f"🚀 Test boshlanmoqda! Tayyorlaning...\n\n⏱ Savollar vaqti: {quiz['time_limit']} soniya")
        await asyncio.sleep(2)
        
        asyncio.create_task(run_group_quiz_loop(chat_id, bot))


async def send_group_results(chat_id, quiz, bot: Bot, is_stopped=False):
    scores = quiz['scores']
    participants = quiz['participants']
    questions = quiz['questions']
    
    sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    
    status_icon = "🚫" if is_stopped else "🏁"
    status_text = "to'xtatildi" if is_stopped else "yakunlandi"
    
    text = f"{status_icon} <b>{quiz['test_title']}</b> testi {status_text}!\n\n"
    text += f"👥 Qatnashuvchilar: {len(participants)} ta\n"
    text += f"❓ Savollar: {len(questions)} ta\n\n"
    text += "📊 <b>TOP NATIJALAR:</b>\n\n"
    
    if not sorted_scores:
        text += "Hech kim qatnashmadi."
    else:
        for i, (u_id, score) in enumerate(sorted_scores, 1):
            name = participants[u_id]
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "🔸"
            text += f"{medal} <a href='tg://user?id={u_id}'>{name}</a> — {score}/{len(questions)} ta\n"
            
    me = await bot.me()
    from urllib.parse import quote
    share_text = f"Men '{quiz['test_title']}' testida qatnashdim! Siz ham o'z bilimingizni sinab ko'ring."
    test_link = f"https://t.me/{me.username}?start=test_{quiz['test_id']}"
    share_url = f"https://t.me/share/url?url={test_link}&text={quote(share_text)}"
    
    builder = InlineKeyboardBuilder()
    builder.button(text="↗️ Testni ulashish", url=share_url)
    
    await bot.send_message(chat_id, text, reply_markup=builder.as_markup())


@router.message(Command("stop"))
async def stop_group_quiz(message: Message, bot: Bot):
    chat_id = message.chat.id
    if chat_id not in group_quizzes:
        return
        
    quiz = group_quizzes[chat_id]
    if message.from_user.id != quiz['admin'] and message.from_user.id not in ADMINS:
        await message.answer("Sizda testni to'xtatish huquqi yo'q!")
        return
        
    quiz['status'] = 'stopped'
    
    if 'current_poll_message_id' in quiz:
        try:
            await bot.stop_poll(chat_id, quiz['current_poll_message_id'])
        except Exception:
            pass
            
    await send_group_results(chat_id, quiz, bot, is_stopped=True)
    del group_quizzes[chat_id]

async def run_group_quiz_loop(chat_id, bot: Bot):
    quiz = group_quizzes.get(chat_id)
    if not quiz: return
    questions = quiz['questions']
    time_limit = quiz['time_limit']
    
    for i, q in enumerate(questions):
        if chat_id not in group_quizzes or group_quizzes[chat_id]['status'] == 'stopped':
            return
            
        quiz['current_q_idx'] = i
        poll_msg = await bot.send_poll(
            chat_id=chat_id,
            question=f"({i+1}/{len(questions)}) {q['question']}",
            options=q['options'],
            type="quiz",
            correct_option_id=q['correct'],
            is_anonymous=False,
            open_period=time_limit
        )
        quiz['current_poll_id'] = poll_msg.poll.id
        quiz['current_poll_message_id'] = poll_msg.message_id
        
        # Checking in small steps to allow instant stop
        for _ in range(int((time_limit + 1.5) * 2)):
            if chat_id not in group_quizzes or group_quizzes[chat_id]['status'] == 'stopped':
                return
            await asyncio.sleep(0.5)
        
    if chat_id in group_quizzes and group_quizzes[chat_id]['status'] != 'stopped':
        await send_group_results(chat_id, quiz, bot, is_stopped=False)
        del group_quizzes[chat_id]
