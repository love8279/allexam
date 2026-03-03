import os
import sys
import types
import asyncio
import requests
import logging

# --- CRITICAL PATCH ---
if "pyrogram.sync" not in sys.modules:
    mock_sync = types.ModuleType("pyrogram.sync")
    mock_sync.async_to_sync = lambda *args, **kwargs: args[0] if args else None
    mock_sync.idle = lambda: None
    mock_sync.compose = lambda *args, **kwargs: None
    sys.modules["pyrogram.sync"] = mock_sync
# ----------------------

from pyrogram import Client, filters
from pyromod import listen
import config

logging.basicConfig(level=logging.INFO)

# Bot Client Setup
bot = Client(
    "AppxBot",
    api_id=config.API_ID,
    api_hash=config.API_HASH,
    bot_token=config.BOT_TOKEN
)

ORG_ID = "53796"

@bot.on_message(filters.command("start") & filters.private)
async def start(bot, message):
    await message.reply_text("✅ **Bot Online Hai!**\n\nAb content nikalne ke liye `/extract` likhein.")

@bot.on_message(filters.command("extract") & filters.private)
async def extract(bot, message):
    try:
        # User details check
        phone = "8279049568"
        password = "8279049568"
        
        status = await message.reply_text("🔑 **Logging in...**")
        
        # Simple Login Request
        login_url = "https://api.appx.co.in/v2/login"
        payload = {"phone": phone, "password": password, "orgId": ORG_ID, "deviceType": "android"}
        res = requests.post(login_url, json=payload).json()
        
        if not res.get("success"):
            return await status.edit(f"❌ Login Error: {res.get('message')}")
            
        token = res["data"]["token"]
        headers = {"token": token}
        
        await status.edit("📚 **Fetching Courses...**")
        courses = requests.get(f"https://api.appx.co.in/v2/get-courses/{ORG_ID}", headers=headers).json()
        
        txt = "🎓 **Available Courses:**\n\n"
        for c in courses.get("data", []):
            txt += f"🔹 `{c['id']}` → **{c['title']}**\n"
        
        await status.edit(txt)
        
        # Asking for Course ID
        cid_msg = await bot.ask(message.chat.id, "🆔 **Enter Course ID:**", timeout=60)
        cid = cid_msg.text.strip()
        
        await message.reply_text(f"⏳ **Extracting ID:** `{cid}`...")
        # ... (rest of the logic)
        
    except Exception as e:
        await message.reply_text(f"❌ Error: {str(e)}")

# Use bot.run() instead of manual loop for stability
if __name__ == "__main__":
    bot.run()
        
