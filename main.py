import sys
import types

# --- PYTHON 3.14 COMPATIBILITY FIX ---
# Pyrogram.sync ko mock karne ka sahi tarika taki error na aaye
if "pyrogram.sync" not in sys.modules:
    mock_sync = types.ModuleType("pyrogram.sync")
    mock_sync.idle = lambda: None
    mock_sync.compose = lambda x: None
    sys.modules["pyrogram.sync"] = mock_sync
# --------------------------------------

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
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Bot Client Setup
bot = Client(
    "AppxBot",
    api_id=config.API_ID,
    api_hash=config.API_HASH,
    bot_token=config.BOT_TOKEN
)

ORG_ID = "53796" # The Excellence Academy

def clean_filename(text):
    return re.sub(r'[\\/*?:"<>|]', "", text).strip()

async def get_token(phone, password):
    url = "https://api.appx.co.in/v2/login"
    payload = {
        "phone": phone, 
        "password": password, 
        "orgId": ORG_ID, 
        "deviceType": "android"
    }
    headers = {"Content-Type": "application/json"}
    try:
        r = requests.post(url, json=payload, headers=headers)
        if r.status_code == 200:
            return r.json()["data"]["token"]
        else:
            raise Exception(r.json().get("message", "Login Failed!"))
    except Exception as e:
        raise Exception(f"API Error: {str(e)}")

@bot.on_message(filters.command(["start"]))
async def start(bot, m: Message):
    await m.reply_text(
        f"👋 **Hello {m.from_user.mention}!**\n\n"
        "The Excellence Academy ka content nikalne ke liye niche diye gaye command ka use karein:\n\n"
        "➡️ `/extract` - To start extraction"
    )

@bot.on_message(filters.command(["extract"]))
async def extract_batch(bot, m: Message):
    try:
        editable = await m.reply_text("🔑 **Logging in to Appx...**")
        
        # Credentials from your earlier input
        token = await get_token("8279049568", "8279049568")
        headers = {"token": token}

        await editable.edit("📚 **Fetching Courses List...**")
        course_res = requests.get(f"https://api.appx.co.in/v2/get-courses/{ORG_ID}", headers=headers).json()
        
        if not course_res.get("data"):
            return await editable.edit("❌ No courses found in this account.")

        listing = "🎓 **Available Courses:**\n\n"
        for c in course_res.get("data", []):
            listing += f"🔹 `{c['id']}` → **{c['title']}**\n"
        
        await editable.edit(listing)

        # Asking for Course ID
        cid_msg = await bot.ask(m.chat.id, "🆔 **Please enter the Course ID to extract:**", timeout=60)
        cid = cid_msg.text.strip()

        process_msg = await m.reply_text(f"⏳ **Extracting content for ID:** `{cid}`...")
        
        # Fetching content
        data_res = requests.get(f"https://api.appx.co.in/v2/get-course-content/{cid}", headers=headers).json()

        if not data_res.get("data"):
            return await process_msg.edit("❌ Is Course ID mein koi data nahi mila.")

        file_name = f"{cid}_Excellence_Academy.txt"
        v_count, p_count = 0, 0

        with open(file_name, "w", encoding="utf-8") as f:
            for item in data_res["data"]:
                title = item.get("title", "Untitled")
                # Checking for different possible URL keys in Appx
                url = item.get("videoUrl") or item.get("pdfUrl") or item.get("vimeoUrl") or item.get("video_link")
                
                if url:
                    f.write(f"{title}: {url}\n")
                    if "pdf" in url.lower() or ".pdf" in url:
                        p_count += 1
                    else:
                        v_count += 1

        caption = (
            f"<b>📦 Extraction Successful!</b>\n\n"
            f"<b>📛 Course ID:</b> <code>{cid}</code>\n"
            f"<b>📊 Stats:</b>\n"
            f"    🎥 Videos: <code>{v_count}</code>\n"
            f"    📄 PDFs: <code>{p_count}</code>\n\n"
            f"<b>🏆 Powered by Gemini</b>"
        )
        
        await m.reply_document(file_name, caption=caption)
        
        # Cleanup
        if os.path.exists(file_name):
            os.remove(file_name)
        await process_msg.delete()

    except Exception as e:
        logger.error(f"Error: {e}")
        await m.reply_text(f"❌ **Error:** `{str(e)}`")

async def start_bot():
    await bot.start()
    logger.info("--- BOT IS LIVE ---")
    await asyncio.Event().wait()

if __name__ == "__main__":
    try:
        asyncio.run(start_bot())
    except KeyboardInterrupt:
        logger.info("--- BOT STOPPED ---")
