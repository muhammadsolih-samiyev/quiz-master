# Telegram Bot (Uzbek)

Bu bot siz so'ragan barcha imkoniyatlarni o'z ichiga oladi:
1. Majburiy a'zolik (obunani tekshirish)
2. Mukammal admin panel
3. Umumiy testlar bo'limi (faqat admin kiritadi)
4. Test yaratish hamma uchun (oddiy foydalanuvchilar o'zi uchun)
5. Mening testlarim bo'limi
6. Kitoblar bo'limi (faqat admin kiritadi)

## O'rnatish
1. `requirements.txt` dagi kutubxonalarni o'rnating:
```bash
pip install -r requirements.txt
```
2. `.env.example` faylidan nusxa olib, yangi `.env` faylini yarating va ichidagi ma'lumotlarni o'zingizga moslang:
- `BOT_TOKEN`: BotFather dan olingan token
- `ADMINS`: Adminlarning Telegram ID raqamlari (vergul bilan ajratilgan)
- `REQUIRED_CHANNELS`: Majburiy a'zolik uchun kanal username lari (@ bilan, vergul bilan ajratilgan)

Eslatma: Majburiy obunani tekshirish ishlashi uchun, botingizni ko'rsatilgan kanallarga Admin qilib qo'shishingiz kerak!

## Ishga tushirish
```bash
python bot.py
```
