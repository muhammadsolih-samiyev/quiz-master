import asyncio
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery
from keyboards.inline import get_subscription_keyboard
from database import get_channels

async def check_channel_member(bot, channel, user_id):
    try:
        member = await bot.get_chat_member(chat_id=channel, user_id=user_id)
        if member.status in ['left', 'kicked', 'banned']:
            return channel
    except Exception as e:
        print(f"Error checking sub for {channel}: {e}")
    return None

class CheckSubscriptionMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data):
        channels = await get_channels()
        if not channels:
            return await handler(event, data)

        bot = data['bot']
        user_id = None

        if isinstance(event, Message):
            user_id = event.from_user.id
        elif isinstance(event, CallbackQuery):
            user_id = event.from_user.id
            if event.data == "check_sub":
                pass

        if user_id:
            tasks = [check_channel_member(bot, ch, user_id) for ch in channels]
            results = await asyncio.gather(*tasks)
            not_subscribed = [ch for ch in results if ch is not None]
            
            if not_subscribed:
                text = "Botdan foydalanish uchun quyidagi kanallarga a'zo bo'lishingiz kerak:"
                markup = get_subscription_keyboard(not_subscribed)
                if isinstance(event, Message):
                    await event.answer(text, reply_markup=markup)
                elif isinstance(event, CallbackQuery):
                    if event.data != "check_sub":
                        await event.message.answer(text, reply_markup=markup)
                    else:
                        await event.answer("Siz hali barcha kanallarga a'zo bo'lmadingiz!", show_alert=True)
                return

        return await handler(event, data)
