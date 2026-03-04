import os
import sys
import types
import asyncio
import requests
import logging
from flask import Flask
from threading import Thread
from pyrogram import Client, filters
from pyromod import listen
from pyrogram.types import Message
import config

# --- KOYEB/HEROKU ANTI-CRASH PATCH ---
if "pyrogram.sync" not in sys.modules:
    mock_sync = types.ModuleType("pyrogram.sync")
    mock_sync.async_to_sync = lambda *args, **kwargs: args[0] if args else None
    mock_sync.idle = lambda: None
    mock_sync.compose = lambda *args, **kwargs: None
    sys.modules["pyrogram.sync"] = mock_sync

# --- DUMMY WEB SERVER FOR KOYEB HEALTH CHECK ---
app = Flask('')

@app.route('/')
def home():
    return "Bot is Alive!"

def run_web():
    # Koyeb default port 8080 use karta hai
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# --- BOT SETUP ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Client(
    "AppxBot",
    api_id=config.API_ID,
    api_hash=config.API_HASH,
    bot_token=config.BOT_TOKEN
)

ORG_ID = "53796"

@bot.on_message(filters.command(["start"]))
async def start(bot, m: Message):
    await m.reply_text("✅ **Bot is Online on Koyeb!**\n\nUse `/extract` to start.")

@bot.on_message(filters.command(["extract"]))
async def extract_batch(bot, m: Message):
    try:
        editable = await m.reply_text("🔑 **Logging in...**")
        
        # Login Logic
        url = "https://api.appx.co.in/v2/login"
        payload = {
            "phone": "8279049568", 
            "password": "8279049568", 
            "orgId": ORG_ID, 
            "deviceType": "android"
        }
        headers = {
            "User-Agent": "Mozilla/5.0 (Linux; Android 10)",
            "Content-Type": "application/json"
        }
        
        r = requests.post(url, json=payload, headers=headers).json()
        
        if not r.get("success"):
            return await editable.edit(f"❌ Login Failed: {r.get('message')}")
            
        token = r["data"]["token"]
        auth_headers = {"token": token, "User-Agent": headers["User-Agent"]}

        await editable.edit("📚 **Fetching Courses...**")
        course_res = requests.get(f"https://api.appx.co.in/v2/get-courses/{ORG_ID}", headers=auth_headers).json()
        
        listing = "🎓 **Available Courses:**\n\n"
        for c in course_res.get("data", []):
            listing += f"🔹 `{c['id']}` → **{c['title']}**\n"
        
        await editable.edit(listing)

        cid_msg = await bot.ask(m.chat.id, "🆔 **Send Course ID:**", timeout=120)
        cid = cid_msg.text.strip()

        process_msg = await m.reply_text(f"⏳ **Extracting...**")
        data_res = requests.get(f"https://api.appx.co.in/v2/get-course-content/{cid}", headers=auth_headers).json()

        file_name = f"{cid}_Content.txt"
        with open(file_name, "w", encoding="utf-8") as f:
            for item in data_res.get("data", []):
                title = item.get("title", "Untitled")
                v_url = item.get("videoUrl") or item.get("pdfUrl") or item.get("vimeoUrl")
                if v_url:
                    f.write(f"{title}: {v_url}\n")

        await m.reply_document(file_name, caption=f"✅ Done for ID: `{cid}`")
        os.remove(file_name)
        await process_msg.delete()

    except Exception as e:
        await m.reply_text(f"❌ **Error:** `{e}`")

# --- EXECUTION ---
if __name__ == "__main__":
    # Web server ko background thread mein chalayein
    t = Thread(target=run_web)
    t.daemon = True
    t.start()
    
    # Bot start karein
    logger.info("Starting Bot...")
    bot.run()
