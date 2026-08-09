import os
import json
import asyncio
from telethon import TelegramClient
from modules.proxy import get_proxy_kwargs

cfg_file = "config.json"
if not os.path.exists(cfg_file):
    print("❌ config.json not found! Please run install.sh first.")
    exit(1)

with open(cfg_file, "r", encoding="utf-8") as f:
    cfg = json.load(f)

is_multi = cfg.get("multi_session", False)
if is_multi:
    print("ℹ️ حالت مولتی سشن (Multi-Session) فعال است.")
    print("🤖 در این حالت نیازی به لاگین دستی در ترمینال نیست!")
    print("لطفاً فایل bot_config.json را تنظیم کرده و main.py را اجرا کنید. کاربران می‌توانند مستقیماً از طریق ربات تلگرام وارد حساب خود شوند.")
    exit(0)

app_id = cfg.get("api_id")
app_hash = cfg.get("api_hash")

proxy_kwargs = get_proxy_kwargs(cfg)
client = TelegramClient("meowace_self", app_id, app_hash, **proxy_kwargs)

async def auth():
    print("⚡ Connecting to Telegram...")
    await client.start()
    me = await client.get_me()
    print(f"\n🎉 Authenticated successfully as {me.first_name} (@{me.username or 'N/A'}) [ID: {me.id}]")
    await client.disconnect()

if __name__ == "__main__":
    asyncio.run(auth())
