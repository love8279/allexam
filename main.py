import sys
import types

# --- CRITICAL FIX FOR PYTHON 3.14 ---
# Ye hissa sabse upar hona chahiye, import se bhi pehle
try:
    if "pyrogram.sync" not in sys.modules:
        mock_sync = types.ModuleType("pyrogram.sync")
        mock_sync.idle = lambda: None
        mock_sync.compose = lambda x: None
        sys.modules["pyrogram.sync"] = mock_sync
except Exception:
    pass
# ------------------------------------

import os
import re
import asyncio
import requests
import logging
from pyrogram import Client, filters
from pyromod import listen
from pyrogram.types import Message
import config

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Bot Client Setup
bot = Client(
    "AppxBot",
    api_id=config.API_ID,
    api_hash=config.API_HASH,
    bot_token=config.BOT_TOKEN
)

ORG_ID = "53796" 

def clean_filename(text):
    return re.sub(r'[\\/*?:"<>|]', "", text).strip()

async def get_token(phone, password):
    url = "https://api.appx.co.in/v2/login"
    payload = {"phone": phone, "password": password, "orgId": ORG_ID, "deviceType": "android"}
    headers = {"Content-Type": "application/json"}
    r = requests.post(url, json=payload, headers=headers)
    if r.status_code == 200:
        return r.json()["data"]["token"]
    raise Exception("Login Failed! Please check credentials.")

@bot.on_message(filters.command(["start"]))
async def start(bot, m: Message):
    await m.reply_text(f"👋 **Hello!**\n\nAcademy content nikalne ke liye `/extract` command ka use karein.")

@bot.on_message(filters.command(["extract"]))
async def extract_batch(bot, m: Message):
    try:
        editable = await m.reply_text("🔑 **Logging in...**")
        token = await get_token("8279049568", "8279049568")
        headers = {"token": token}

        await editable.edit("📚 **Fetching Courses...**")
        course_res = requests.get(f"https://api.appx.co.in/v2/get-courses/{ORG_ID}", headers=headers).json()
        
        listing = "🎓 **Available Courses:**\n\n"
        for c in course_res.get("data", []):
            listing += f"🔹 `{c['id']}` → **{c['title']}**\n"
        
        await editable.edit(listing)

        cid_msg = await bot.ask(m.chat.id, "🆔 **Enter Course ID:**", timeout=60)
        cid = cid_msg.text.strip()

        process_msg = await m.reply_text(f"⏳ **Extracting...**")
        data_res = requests.get(f"https://api.appx.co.in/v2/get-course-content/{cid}", headers=headers).json()

        if not data_res.get("data"):
            return await process_msg.edit("❌ No data found.")

        file_name = f"{cid}_Content.txt"
        v_count, p_count = 0, 0

        with open(file_name, "w", encoding="utf-8") as f:
            for item in data_res["data"]:
                title = item.get("title", "Untitled")
                url = item.get("videoUrl") or item.get("pdfUrl") or item.get("vimeoUrl")
                if url:
                    f.write(f"{title}: {url}\n")
                    if "pdf" in url.lower(): p_count += 1
                    else: v_count += 1

        await m.reply_document(file_name, caption=f"🎥 Videos: {v_count}\n📄 PDFs: {p_count}")
        os.remove(file_name)
        await process_msg.delete()

    except Exception as e:
        await m.reply_text(f"❌ **Error:** `{e}`")

async def run_bot():
    async with bot:
        logger.info("Bot is Up!")
        await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(run_bot())
