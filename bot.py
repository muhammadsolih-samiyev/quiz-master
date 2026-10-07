import asyncio
import sys
import logging
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session.aiohttp import AiohttpSession

from config import BOT_TOKEN, PROXY_URL
from database import init_db
from middlewares.check_sub import CheckSubscriptionMiddleware

from handlers.user import router as user_router
from handlers.admin import router as admin_router
from handlers.tests import router as tests_router
from handlers.books import router as books_router
from handlers.quiz import router as quiz_router

async def main():
    logging.basicConfig(level=logging.INFO)
    await init_db()

    if PROXY_URL:
        session = AiohttpSession(proxy=PROXY_URL)
        bot = Bot(token=BOT_TOKEN, session=session, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
        print(f"Bot proxy orqali ulanmoqda: {PROXY_URL}")
    else:
        bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

    dp = Dispatcher()

    dp.message.middleware(CheckSubscriptionMiddleware())
    dp.callback_query.middleware(CheckSubscriptionMiddleware())

    dp.include_router(quiz_router)
    dp.include_router(user_router)
    dp.include_router(admin_router)
    dp.include_router(tests_router)
    dp.include_router(books_router)

    from aiohttp import web
    import os

    async def health_check(request):
        return web.Response(text="Bot is alive!")

    app = web.Application()
    app.router.add_get('/', health_check)
    runner = web.AppRunner(app)
    await runner.setup()
    
    port = int(os.environ.get("PORT", 10000))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    print(f"Web server started on port {port}")

    try:
        print("Bot is starting...")
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

if __name__ == "__main__":
    # Windows-da ProactorEventLoop WinError 121 beradigan muammoni hal qilish
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("Bot stopped.")
