import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
ADMINS = [int(admin_id) for admin_id in os.getenv("ADMINS", "").split(",") if admin_id]
PROXY_URL = os.getenv("PROXY_URL", "")  # masalan: socks5://user:pass@host:port yoki http://host:port
